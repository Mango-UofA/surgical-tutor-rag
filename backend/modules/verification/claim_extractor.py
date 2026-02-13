"""
Claim Extractor for Graph-Based Verification
Extracts verifiable factual claims from generated answers.
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


class ClaimExtractor:
    """
    Extracts structured factual claims from surgical answers for verification.
    Focuses on instrument-step pairs, step ordering, and anatomy-procedure links.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL
        
        self.client = OpenAIClient(
            api_key=self.api_key,
            base_url=self.base_url
        ) if self.api_key else None
    
    def extract_claims(self, answer: str, query: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract structured claims from the answer.
        
        Args:
            answer: Generated answer text
            query: Original query (for context)
        
        Returns:
            Dictionary with claim categories:
            - instrument_claims: {step, instrument, context}
            - step_order_claims: {procedure, step1, step2, relationship}
            - anatomy_claims: {procedure, anatomical_structure, relationship}
            - complication_claims: {procedure, complication, management}
        """
        if not self.client:
            logger.error("OpenAI client not configured")
            return self._empty_claims()
        
        extraction_prompt = self._build_extraction_prompt(answer, query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical claim extraction expert. Extract only factual, verifiable claims in structured JSON format."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            claims_json = response.choices[0].message.content
            claims = json.loads(claims_json)
            
            # Validate structure
            return self._validate_claims(claims)
            
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return self._empty_claims()
    
    def _build_extraction_prompt(self, answer: str, query: str) -> str:
        """Build the extraction prompt with examples."""
        return f"""Extract structured factual claims from this surgical answer. Return ONLY valid JSON.

Query: {query}

Answer: {answer}

Extract claims in these categories (return empty arrays if none found):

1. **instrument_claims**: Tools/instruments used in specific steps
   Format: {{"step": "step name", "instrument": "instrument name", "usage": "how it's used"}}

2. **step_order_claims**: Sequential relationships between procedure steps
   Format: {{"procedure": "procedure name", "step_before": "first step", "step_after": "next step", "relationship": "PRECEDES|FOLLOWS|REQUIRES"}}

3. **anatomy_claims**: Anatomical structures involved in procedures
   Format: {{"procedure": "procedure name", "anatomical_structure": "structure name", "relationship": "INVOLVES|TARGETS|AVOIDS|IDENTIFIES"}}

4. **complication_claims**: Complications and their management
   Format: {{"procedure": "procedure name", "complication": "complication name", "management": "management approach"}}

CRITICAL: Return ONLY valid JSON with this exact structure:
{{
    "instrument_claims": [...],
    "step_order_claims": [...],
    "anatomy_claims": [...],
    "complication_claims": [...]
}}

Extract clear, specific claims. If a claim is vague or uncertain, omit it.
"""
    
    def _validate_claims(self, claims: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Validate and standardize claim structure."""
        validated = {
            "instrument_claims": [],
            "step_order_claims": [],
            "anatomy_claims": [],
            "complication_claims": []
        }
        
        for key in validated.keys():
            if key in claims and isinstance(claims[key], list):
                validated[key] = claims[key]
        
        return validated
    
    def _empty_claims(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return empty claims structure."""
        return {
            "instrument_claims": [],
            "step_order_claims": [],
            "anatomy_claims": [],
            "complication_claims": []
        }
    
    def count_total_claims(self, claims: Dict[str, List[Dict[str, Any]]]) -> int:
        """Count total extractable claims across all categories."""
        return sum(len(claim_list) for claim_list in claims.values())
