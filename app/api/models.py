from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., description="Detective's question or investigation query")

class DocumentResponse(BaseModel):
    id: str
    text: str
    score: float
    confidence: str
    metadata: Dict[str, Any]
    vector_score: Optional[float] = None
    relevance_score: Optional[float] = None

class RetrievalResponse(BaseModel):
    documents: List[DocumentResponse]
    strategy: str
    expanded_queries: Optional[List[str]] = None

class ReportResponse(BaseModel):
    report: str
    query: str
    timestamp: str
    evidence_count: Optional[int] = None
    retrieval_strategy: Optional[str] = None
    error: Optional[bool] = None
    is_relevant: Optional[bool] = None
    rejection_reason: Optional[str] = None

class S3Response(BaseModel):
    success: bool
    report_id: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

class InvestigationResponse(BaseModel):
    query: str
    retrieval: RetrievalResponse
    report: ReportResponse
    storage: S3Response