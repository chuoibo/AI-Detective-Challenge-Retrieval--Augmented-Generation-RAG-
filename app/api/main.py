from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.models import QueryRequest, InvestigationResponse
from app.rag.retriever import DocumentRetriever
from app.rag.reranker import DocumentReranker
from app.rag.llm import ReportGenerator
from app.rag.guard_agent import GuardAgent
from app.db.s3_storage import S3Storage
from app.core.config import settings
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_retriever():
    return DocumentRetriever()

def get_reranker():
    return DocumentReranker()

def get_report_generator():
    return ReportGenerator()

def get_s3_storage():
    return S3Storage()

def get_guard_agent():
    return GuardAgent()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto Detective RAG API"}

@app.post(f"{settings.API_V1_STR}/investigate", response_model=InvestigationResponse)
async def investigate(
    request: QueryRequest,
    retriever: DocumentRetriever = Depends(get_retriever),
    reranker: DocumentReranker = Depends(get_reranker),
    report_generator: ReportGenerator = Depends(get_report_generator),
    s3_storage: S3Storage = Depends(get_s3_storage),
    guard_agent: GuardAgent = Depends(get_guard_agent)
):

    try:
        logger.info(f"Processing investigation query: {request.query}")
        
        is_relevant, reason = guard_agent.is_query_relevant(request.query)
        
        if not is_relevant:
            logger.warning(f"Rejected irrelevant query: '{request.query}'. Reason: {reason}")
            
            rejection = guard_agent.generate_rejection_response(request.query, reason)
            
            return InvestigationResponse(
                query=request.query,
                retrieval={
                    "documents": [],
                    "strategy": "none",
                    "expanded_queries": None
                },
                report={
                    "report": rejection["message"],
                    "query": request.query,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": True,
                    "is_relevant": False,
                    "rejection_reason": reason
                },
                storage={
                    "success": False,
                    "error": "Query rejected as irrelevant to investigation"
                }
            )
        
        logger.info(f"Query validated as relevant: {reason}")
        
        retrieval_result = retriever.retrieve(request.query)
        
        reranked_documents = reranker.rerank_documents(
            query=request.query,
            documents=retrieval_result["documents"]
        )
        
        retrieval_result["documents"] = reranked_documents
        
        report_data = report_generator.generate_report(
            query=request.query,
            documents=reranked_documents,
            retrieval_info=retrieval_result
        )
        
        storage_result = s3_storage.save_report(report_data)
        
        return InvestigationResponse(
            query=request.query,
            retrieval=retrieval_result,
            report=report_data,
            storage=storage_result
        )
        
    except Exception as e:
        logger.error(f"Error processing investigation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    return {"status": "healthy"}