import openai
from typing import List, Dict, Any
from app.core.config import settings
import datetime

class ReportGenerator:
    def __init__(self):
        self.model = settings.LLM_MODEL
        
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )
    
    def generate_report(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        retrieval_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an investigation report based on the retrieved documents.
        
        Args:
            query: The detective's original query
            documents: List of reranked documents
            retrieval_info: Additional information about the retrieval process
            
        Returns:
            Dictionary containing the generated report and metadata
        """
        # Prepare context from documents
        document_context = "\n\n".join([
            f"DOCUMENT {i+1} (Confidence: {doc['confidence']}):\n{doc['text']}"
            for i, doc in enumerate(documents)
        ])
        
        # Include retrieval strategy information
        strategy_info = ""
        if retrieval_info["strategy"] == "multi-step":
            expanded_queries = retrieval_info.get("expanded_queries", [])
            if expanded_queries:
                strategy_info = "Expanded search queries used:\n" + "\n".join([
                    f"- {query}" for query in expanded_queries
                ])
        
        # Current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build prompt for the LLM
        prompt = f"""
        You are an AI assistant for detectives investigating a major cryptocurrency exchange hack.
        Based on the detective's query and the provided case evidence, generate a detailed investigation report.
        
        Detective's Query: {query}
        
        Evidence from Case Files:
        {document_context}
        
        {strategy_info}
        
        Create a comprehensive investigation report that includes:
        1. SUMMARY: A brief overview of findings related to the query
        2. KEY EVIDENCE: Highlight the most important pieces of evidence found
        3. ANALYSIS: Detailed analysis of the evidence and its implications for the case
        4. CONNECTIONS: Any connections between different evidence or potential leads
        5. NEXT STEPS: Recommended actions for the investigation team
        
        The report should be professional, fact-based, and clearly cite which document(s) each piece of information comes from.
        Be extremely careful not to include speculative information that isn't supported by the evidence.
        When evidence is contradictory, clearly note the contradictions.
        """
        
        # Generate report using LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a criminal investigation AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            report_content = response.choices[0].message.content
            
            return {
                "report": report_content,
                "query": query,
                "timestamp": timestamp,
                "evidence_count": len(documents),
                "retrieval_strategy": retrieval_info["strategy"]
            }
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return {
                "report": f"Error generating report: {str(e)}",
                "query": query,
                "timestamp": timestamp,
                "error": True
            }