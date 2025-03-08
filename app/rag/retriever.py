import openai
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.db.pinecone_db import PineconeDB
import json

class DocumentRetriever:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )
        self.pinecone_db = PineconeDB()
        self.strategy = settings.RETRIEVAL_STRATEGY
        self.top_k = settings.TOP_K_RETRIEVAL
    
    def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=[text],
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    
    def single_step_retrieval(self, query: str) -> List[Dict[str, Any]]:
        query_embedding = self.get_embedding(query)
        return self.pinecone_db.similarity_search(
            query_embedding=query_embedding,
            top_k=self.top_k
        )
    
    def generate_search_queries(self, query: str) -> List[str]:
        """Use LLM to generate multiple search queries for the original query."""
        prompt = f"""
        You are an expert detective working on a crypto exchange hack case.
        Given the following investigation question, generate 3 specific search queries that would help
        find relevant evidence in our case files.
        
        Original question: {query}
        
        Output the search queries as a JSON array of strings. Each query should focus on different aspects
        of the investigation. Be specific and use technical terms related to cryptocurrency, cyber security,
        and digital forensics where appropriate.
        """
        
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a criminal investigation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        try:
            content = response.choices[0].message.content
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                queries = json.loads(json_str)
                return queries
            else:
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                queries = [line.split(":", 1)[-1].strip() for line in lines if ":" in line]
                return queries[:3] + [query]  
        except Exception as e:
            print(f"Error parsing LLM output: {e}")
            return [query]
    
    def multi_step_retrieval(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        expanded_queries = self.generate_search_queries(query)
        
        all_results = []
        
        for expanded_query in expanded_queries:
            query_embedding = self.get_embedding(expanded_query)
            results = self.pinecone_db.similarity_search(
                query_embedding=query_embedding,
                top_k=self.top_k // len(expanded_queries) + 1  
            )
            all_results.extend(results)
        
        unique_results = {}
        for result in all_results:
            if result["id"] not in unique_results or result["score"] > unique_results[result["id"]]["score"]:
                unique_results[result["id"]] = result
        
        final_results = sorted(
            list(unique_results.values()),
            key=lambda x: x["score"],
            reverse=True
        )[:self.top_k]
        
        return final_results, expanded_queries
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        if self.strategy == "single-step":
            results = self.single_step_retrieval(query)
            return {
                "documents": results,
                "strategy": "single-step",
                "expanded_queries": None
            }
        else: 
            results, expanded_queries = self.multi_step_retrieval(query)
            return {
                "documents": results,
                "strategy": "multi-step",
                "expanded_queries": expanded_queries
            }