"""
Multi-Step Query Decomposition
Breaks down complex surgical queries into multiple sub-queries for better retrieval.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI as OpenAIClient
import os
import json
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class QueryDecomposer:
    """
    Decomposes complex surgical queries into simpler sub-queries.
    
    Example:
        Input: "What are the steps for laparoscopic appendectomy, 
                what instruments are needed, and how do you handle a perforated appendix?"
        
        Output: [
            "What are the steps for laparoscopic appendectomy?",
            "What instruments are needed for laparoscopic appendectomy?",
            "How do you handle a perforated appendix during laparoscopic appendectomy?"
        ]
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL
        
        self.client = OpenAIClient(
            api_key=self.api_key,
            base_url=self.base_url
        ) if self.api_key else None
        
        self.max_subqueries = 4  # Limit to prevent over-decomposition
    
    def decompose(self, query: str) -> List[str]:
        """
        Decompose a query into sub-queries if it's complex.
        
        Args:
            query: Original user query
        
        Returns:
            List of sub-queries. If query is simple, returns [original_query].
            If decomposition fails, returns [original_query].
        """
        if not self.client:
            logger.error("OpenAI client not configured")
            return [query]
        
        # Quick check: if query is short and simple, don't decompose
        if len(query.split()) < 15 and ',' not in query and ' and ' not in query.lower():
            logger.info("Query is simple, no decomposition needed")
            return [query]
        
        decomposition_prompt = self._build_decomposition_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing surgical questions and breaking them into focused sub-questions. Return ONLY valid JSON."},
                    {"role": "user", "content": decomposition_prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            result = json.loads(result_json)
            
            subqueries = result.get("subqueries", [])
            
            # Validate and limit subqueries
            if not subqueries or not isinstance(subqueries, list):
                logger.warning("Invalid decomposition result, using original query")
                return [query]
            
            # Limit to max_subqueries
            subqueries = subqueries[:self.max_subqueries]
            
            # Filter out empty strings
            subqueries = [sq.strip() for sq in subqueries if sq.strip()]
            
            if not subqueries:
                return [query]
            
            logger.info(f"Decomposed query into {len(subqueries)} sub-queries")
            return subqueries
            
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return [query]
    
    def _build_decomposition_prompt(self, query: str) -> str:
        """Build the decomposition prompt."""
        return f"""Analyze this surgical question and decompose it into 2-4 focused sub-questions if it contains multiple distinct aspects.

Original Question:
{query}

Guidelines:
- If the question asks about multiple topics (e.g., steps + instruments + complications), split them
- Each sub-question should be self-contained and specific
- Preserve the procedure name in each sub-question for context
- Keep technical terminology intact
- If the question is already focused on ONE topic, return it as a single sub-question
- Maximum 4 sub-questions

Return ONLY valid JSON in this exact format:
{{
    "is_complex": true/false,
    "subqueries": [
        "sub-question 1",
        "sub-question 2",
        ...
    ]
}}

Examples:

Input: "What are the steps for laparoscopic cholecystectomy?"
Output: {{"is_complex": false, "subqueries": ["What are the steps for laparoscopic cholecystectomy?"]}}

Input: "What are the steps for laparoscopic appendectomy, what instruments are needed, and how do you handle a perforated appendix?"
Output: {{
    "is_complex": true,
    "subqueries": [
        "What are the steps for laparoscopic appendectomy?",
        "What instruments are needed for laparoscopic appendectomy?",
        "How do you manage a perforated appendix during laparoscopic appendectomy?"
    ]
}}

Input: "Describe thyroidectomy procedure including anatomy, steps, and key safety considerations"
Output: {{
    "is_complex": true,
    "subqueries": [
        "What is the relevant anatomy for thyroidectomy?",
        "What are the steps of thyroidectomy?",
        "What are the key safety considerations during thyroidectomy?"
    ]
}}

Now decompose the given question.
"""
    
    def should_decompose(self, query: str) -> bool:
        """
        Quick heuristic check if query might benefit from decomposition.
        
        Args:
            query: User query
        
        Returns:
            True if query appears complex enough to decompose
        """
        # Simple heuristics
        indicators = [
            len(query.split()) > 15,  # Long query
            query.count(',') >= 2,  # Multiple clauses
            ' and ' in query.lower(),  # Conjunction
            '?' in query[:-1],  # Multiple questions
            any(word in query.lower() for word in ['steps', 'instruments', 'complications', 'anatomy', 'management'])
        ]
        
        return sum(indicators) >= 2
