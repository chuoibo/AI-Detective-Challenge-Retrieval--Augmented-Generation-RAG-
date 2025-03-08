from app.rag.embeddings import EmbeddingProcessor
from app.db.pinecone_db import PineconeDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.embedding_processor = EmbeddingProcessor()
        self.pinecone_db = PineconeDB()
    
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