import openai
from typing import List, Dict, Any
from app.core.config import settings

class DocumentReranker:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        self.top_k = settings.TOP_K_RERANK
    
    def rerank_documents(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not documents:
            return []
        
        batch_size = min(5, len(documents))  
        reranked_docs = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            prompts = []
            for doc in batch:
                prompt = f"""
                Rate the relevance of this document to the detective's query on a scale of 0-100.
                
                Detective's Query: {query}
                
                Document:
                {doc["text"]}
                
                Consider:
                1. Direct evidence related to the crypto hack
                2. Technical details about cryptocurrency transactions
                3. Suspect identification information
                4. Timeline of events
                5. Methods used in the attack
                
                Provide your rating as a single number between 0 and 100, where:
                - 0-20: Not relevant at all
                - 21-40: Slightly relevant but mostly off-topic
                - 41-60: Moderately relevant with some useful information
                - 61-80: Highly relevant with important evidence
                - 81-100: Extremely relevant, contains critical evidence
                
                Output only the number.
                """
                prompts.append(prompt)
            
            llm_scores = []
            for prompt in prompts:
                try:
                    response = self.client.chat.completions.create(
                        model=settings.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a criminal investigation assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=50
                    )
                    
                    score_text = response.choices[0].message.content.strip()
                    digits = ''.join(c for c in score_text if c.isdigit())
                    score = int(digits) if digits else 0
                    
                    score = max(0, min(100, score))
                    llm_scores.append(score / 100.0)  
                    
                except Exception as e:
                    print(f"Error getting LLM score: {e}")
                    llm_scores.append(batch[len(llm_scores)]["score"])
            

            for j, doc in enumerate(batch):
                vector_score = doc["score"]
                llm_score = llm_scores[j]
                combined_score = 0.4 * vector_score + 0.6 * llm_score
                
                reranked_docs.append({
                    **doc,
                    "score": combined_score,
                    "vector_score": vector_score,
                    "relevance_score": llm_score,
                    "confidence": self._get_confidence_label(combined_score)
                })
        
        reranked_docs = sorted(reranked_docs, key=lambda x: x["score"], reverse=True)[:self.top_k]
        
        return reranked_docs
    
    def _get_confidence_label(self, score: float) -> str:
        if score >= 0.8:
            return "Very High"
        elif score >= 0.6:
            return "High"
        elif score >= 0.4:
            return "Medium"
        elif score >= 0.2:
            return "Low"
        else:
            return "Very Low"