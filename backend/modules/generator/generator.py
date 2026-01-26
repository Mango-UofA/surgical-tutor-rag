import os
from typing import List, Dict, Any, Optional
from openai import OpenAI as OpenAIClient

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class Generator:
    def __init__(self, openai_api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL
        # Use OpenAI client with custom base URL for OpenRouter support
        self.client = OpenAIClient(
            api_key=self.openai_api_key,
            base_url=self.base_url
        ) if self.openai_api_key else None

    def generate_answer(self, query: str, contexts: List[Dict[str, Any]], level: str = "Novice") -> str:
        """
        Build a prompt with retrieved contexts and call the LLM. Keep the response educational-only.
        """
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        context_texts = "\n\n".join([c.get("metadata", {}).get("text", "") for c in contexts])
        prompt = f"You are an educational surgical tutor. Do NOT provide clinical advice. "
        prompt += f"Level: {level}.\n\nContext:\n{context_texts}\n\nQuestion:\n{query}\n\nAnswer concisely and include citations to the context segments when possible."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

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
