import pinecone
from typing import List, Dict, Any, Optional
from app.core.config import settings

class PineconeDB:
    def __init__(self):
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        if settings.PINECONE_INDEX not in pinecone.list_indexes():
            pinecone.create_index(
                name=settings.PINECONE_INDEX,
                dimension=1536,  
                metric="cosine"
            )
        
        self.index = pinecone.Index(settings.PINECONE_INDEX)
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
    
    def delete_all(self) -> None:
        """Delete all vectors in the namespace."""
        self.index.delete(deleteAll=True, namespace=self.namespace)