from pinecone import Pinecone
from typing import List, Dict, Any, Optional
from app.core.config import settings

class PineconeDB:
    def __init__(self):
        pc = Pinecone(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        self.index = pc.Index(settings.PINECONE_INDEX)
        self.namespace = settings.PINECONE_NAMESPACE
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace,
            filter=filter
        )
        
        documents = []
        for match in results["matches"]:
            documents.append({
                "id": match["id"],
                "score": match["score"],
                "text": match["metadata"]["text"],
                "metadata": {
                    k: v for k, v in match["metadata"].items() if k != "text"
                }
            })
        
        return documents
    
