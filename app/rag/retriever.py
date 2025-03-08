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
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            input=[text],
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    
    def single_step_retrieval(self, query: str) -> List[Dict[str, Any]]:
        """Simple retrieval that directly matches the query with documents."""
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
        
        response = openai.ChatCompletion.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a criminal investigation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        # Extract generated queries from the response
        try:
            content = response.choices[0].message.content
            # Look for JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                queries = json.loads(json_str)
                return queries
            else:
                # Fallback if JSON parsing fails
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                queries = [line.split(":", 1)[-1].strip() for line in lines if ":" in line]
                return queries[:3] + [query]  # Include original query as backup
        except Exception as e:
            print(f"Error parsing LLM output: {e}")
            # Fallback to original query
            return [query]
    
    def multi_step_retrieval(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Advanced retrieval that expands the query and retrieves documents in multiple steps.
        Returns both the retrieved documents and the expanded queries used.
        """
        # Step 1: Generate multiple search queries
        expanded_queries = self.generate_search_queries(query)
        
        # Step 2: Get embeddings for all queries
        all_results = []
        
        # Step 3: Execute each query and collect results
        for expanded_query in expanded_queries:
            query_embedding = self.get_embedding(expanded_query)
            results = self.pinecone_db.similarity_search(
                query_embedding=query_embedding,
                top_k=self.top_k // len(expanded_queries) + 1  # Distribute top_k among queries
            )
            all_results.extend(results)
        
        # Step 4: Remove duplicates based on document ID
        unique_results = {}
        for result in all_results:
            if result["id"] not in unique_results or result["score"] > unique_results[result["id"]]["score"]:
                unique_results[result["id"]] = result
        
        # Step 5: Sort by score and limit to top_k
        final_results = sorted(
            list(unique_results.values()),
            key=lambda x: x["score"],
            reverse=True
        )[:self.top_k]
        
        return final_results, expanded_queries
    
    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Retrieve documents based on the configured strategy.
        Returns both the retrieved documents and additional info about the retrieval process.
        """
        if self.strategy == "single-step":
            results = self.single_step_retrieval(query)
            return {
                "documents": results,
                "strategy": "single-step",
                "expanded_queries": None
            }
        else:  # multi-step
            results, expanded_queries = self.multi_step_retrieval(query)
            return {
                "documents": results,
                "strategy": "multi-step",
                "expanded_queries": expanded_queries
            }