import openai
from typing import Dict, Any, Tuple
from app.core.config import settings
import re

class GuardAgent:
    """
    A guard agent that validates user queries to ensure they're related to the
    crypto exchange hack investigation and filter out irrelevant or off-topic requests.
    """
    
    def __init__(self):
        self.model = settings.LLM_MODEL
        # List of relevant topics for the investigation
        self.relevant_topics = [
            "cryptocurrency", "crypto", "exchange", "hack", "hacker", "theft", "stolen", 
            "blockchain", "transaction", "wallet", "bitcoin", "ethereum", "evidence", 
            "investigation", "trace", "forensic", "security", "breach", "attack", 
            "exploit", "vulnerability", "suspect", "money laundering", "tumbler", "mixer",
            "tracking", "addresses", "keys", "digital", "transfer", "suspicious", "activity",
            "anonymity", "pseudonymous", "signature", "ledger", "timestamp", "record", 
            "analysis", "pattern", "behavior", "identity", "method", "technique", "tool",
            "trail", "cover tracks", "obfuscation", "$5 million"
        ]
    
    def is_query_relevant(self, query: str) -> Tuple[bool, str]:
        """
        Check if a user query is relevant to the crypto exchange hack investigation.
        
        Args:
            query: The user's query
            
        Returns:
            A tuple of (is_relevant, reason)
        """
        # Simple keyword check as first filter
        query_lower = query.lower()
        keyword_match = any(topic.lower() in query_lower for topic in self.relevant_topics)
        
        # If no keywords match, query is likely irrelevant
        if not keyword_match:
            # Double check with LLM to reduce false negatives
            return self._validate_with_llm(query)
        
        # If keywords match, it's likely relevant
        return True, "Query contains investigation-related keywords"
    
    def _validate_with_llm(self, query: str) -> Tuple[bool, str]:
        """
        Use LLM to validate if a query is relevant to the investigation.
        """
        try:
            prompt = f"""
            You are a security system for a detective AI that only answers questions about a cryptocurrency exchange hack investigation.
            
            The investigation involves:
            - A crypto exchange hack where $5 million was stolen
            - Analysis of blockchain transactions and wallet activity
            - Tracking how the hacker covered their tracks
            - Digital forensics and cryptocurrency security
            
            Determine if the following query is relevant to this investigation:
            
            Query: {query}
            
            First, explain your reasoning about whether this query relates to the cryptocurrency hack investigation.
            
            Then, make your final determination with one of these exact phrases:
            - "RELEVANT: This query is about the crypto hack investigation"
            - "IRRELEVANT: This query is not about the crypto hack investigation"
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security evaluation system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            
            # Extract the determination and explanation
            if "RELEVANT:" in content:
                return True, self._extract_explanation(content)
            elif "IRRELEVANT:" in content:
                return False, self._extract_explanation(content)
            else:
                # Fallback if no clear determination
                contains_keywords = ["crypto", "hack", "exchange", "investigation"]
                if any(keyword in content.lower() for keyword in contains_keywords):
                    return True, "Query might be related to the investigation"
                return False, "Query appears to be unrelated to the investigation"
        
        except Exception as e:
            # In case of API error, be inclusive rather than exclusive
            return True, f"Error validating query, proceeding with caution: {str(e)}"
    
    def _extract_explanation(self, content: str) -> str:
        """Extract a clean explanation from the LLM response."""
        # Try to find the explanation part before the determination
        parts = content.split("RELEVANT:") if "RELEVANT:" in content else content.split("IRRELEVANT:")
        
        if len(parts) > 1:
            # The explanation is likely in the first part
            explanation = parts[0].strip()
        else:
            # Fallback - use the whole response
            explanation = content.strip()
        
        # Clean up and truncate the explanation
        explanation = re.sub(r'\s+', ' ', explanation)  # Normalize whitespace
        if len(explanation) > 150:
            explanation = explanation[:147] + "..."
        
        return explanation
    
    def generate_rejection_response(self, query: str, reason: str) -> Dict[str, Any]:
        """
        Generate a structured response for rejected queries.
        
        Args:
            query: The user's query
            reason: Reason for rejection
            
        Returns:
            Dictionary with rejection information
        """
        return {
            "query": query,
            "is_relevant": False,
            "reason": reason,
            "message": "I'm sorry, I can only answer questions related to the cryptocurrency exchange hack investigation. Your query appears to be unrelated to this case."
        }