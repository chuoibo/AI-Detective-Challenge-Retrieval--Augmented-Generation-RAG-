from app.rag.embeddings import EmbeddingProcessor
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InitPineCone:
    def __init__(self):
        pc = Pinecone(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        if settings.PINECONE_INDEX not in pc.list_indexes():
            pc.create_index(
                name=settings.PINECONE_INDEX,
                dimension=1536,  
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        self.index = pc.Index(settings.PINECONE_INDEX)
        self.namespace = settings.PINECONE_NAMESPACE

    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        vectors = []
        
        for doc in documents:
            vectors.append({
                "id": doc["id"],
                "values": doc["embedding"],
                "metadata": {
                    "text": doc["text"],
                    **doc["metadata"]
                }
            })
        
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=self.namespace)

    def delete_all(self) -> None:
        stats = self.index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        
        if self.namespace in namespaces:
            self.index.delete(deleteAll=True, namespace=self.namespace)
        else:
            print(f"Namespace '{self.namespace}' doesn't exist yet. Nothing to delete.")


class DocumentService:
    def __init__(self):
        self.embedding_processor = EmbeddingProcessor()
        self.pinecone_db = InitPineCone()
    
    def load_all_documents(self) -> dict:
        try:
            logger.info("Starting document loading process")
            
            processed_chunks = self.embedding_processor.process_case_files()
            
            logger.info(f"Generated {len(processed_chunks)} chunks from case files")
            
            self.pinecone_db.upsert_documents(processed_chunks)
            
            logger.info("Successfully uploaded documents to Pinecone")
            
            return {
                "success": True,
                "chunk_count": len(processed_chunks),
                "message": "Documents successfully loaded and embedded"
            }
            
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to load documents"
            }
    
    def clear_documents(self) -> dict:
        try:
            logger.info("Clearing all documents from Pinecone")
            
            self.pinecone_db.delete_all()
            
            return {
                "success": True,
                "message": "All documents successfully removed from database"
            }
            
        except Exception as e:
            logger.error(f"Error clearing documents: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to clear documents"
            }