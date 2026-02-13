import os
from typing import List, Dict, Any, Optional
from openai import OpenAI as OpenAIClient
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class Generator:
    def __init__(self, 
                 openai_api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, 
                 model: Optional[str] = None,
                 verification_pipeline = None,
                 surgical_cot_prompter = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL
        self.verification_pipeline = verification_pipeline
        self.surgical_cot_prompter = surgical_cot_prompter
        
        # Use OpenAI client with custom base URL for OpenRouter support
        self.client = OpenAIClient(
            api_key=self.openai_api_key,
            base_url=self.base_url
        ) if self.openai_api_key else None

    def generate_answer(self, 
                       query: str, 
                       contexts: List[Dict[str, Any]], 
                       level: str = "Novice",
                       enable_verification: bool = True,
                       use_surgical_cot: bool = True) -> Dict[str, Any]:
        """
        Build a prompt with retrieved contexts and call the LLM. Keep the response educational-only.
        
        Args:
            query: User question
            contexts: Retrieved context chunks
            level: Educational level (Novice/Intermediate/Advanced)
            enable_verification: Whether to verify answer against graph
            use_surgical_cot: Whether to use surgical Chain-of-Thought prompting
        
        Returns:
            Dictionary with answer, verification results, and metadata
        """
        if not self.client:
            return {
                "answer": "Error: OpenAI API key not configured",
                "verification": None
            }
        
        # Choose prompt strategy
        if use_surgical_cot and self.surgical_cot_prompter:
            prompt = self.surgical_cot_prompter.build_adaptive_cot_prompt(query, contexts, level)
            logger.info("Using surgical Chain-of-Thought prompting")
        else:
            # Standard prompt
            context_texts = "\n\n".join([c.get("metadata", {}).get("text", "") for c in contexts])
            prompt = f"You are an educational surgical tutor. Do NOT provide clinical advice. "
            prompt += f"Level: {level}.\n\nContext:\n{context_texts}\n\nQuestion:\n{query}\n\nAnswer concisely and include citations to the context segments when possible."
            logger.info("Using standard prompting")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800  # Increased for CoT reasoning
            )
            answer_text = response.choices[0].message.content
            
            # Perform verification if enabled and pipeline available
            verification_report = None
            if enable_verification and self.verification_pipeline:
                try:
                    logger.info("Running answer verification...")
                    verification_report = self.verification_pipeline.verify_answer(query, answer_text)
                    
                    # Append verification summary to answer
                    verification_summary = self.verification_pipeline.format_verification_for_user(verification_report)
                    answer_text += verification_summary
                    
                except Exception as e:
                    logger.error(f"Verification failed: {e}")
                    verification_report = {"error": str(e)}
            
            return {
                "answer": answer_text,
                "verification": verification_report,
                "used_surgical_cot": use_surgical_cot and self.surgical_cot_prompter is not None
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "verification": None,
                "used_surgical_cot": False
            }

    def generate_quiz(self, contexts: List[Dict[str, Any]], level: str = "Novice") -> Dict[str, Any]:
        # simple placeholder — in production use a template and structured output
        if not self.client:
            return {"quiz_text": "Error: OpenAI API key not configured"}
        
        prompt = f"Create a short {level} quiz (5 Qs) with answers from the context. Context: \n"
        prompt += "\n\n".join([c.get("metadata", {}).get("text", "") for c in contexts])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return {"quiz_text": response.choices[0].message.content}
        except Exception as e:
            return {"quiz_text": f"Error generating quiz: {str(e)}"}
