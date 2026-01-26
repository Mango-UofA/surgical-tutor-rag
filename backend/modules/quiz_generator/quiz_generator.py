from typing import List, Dict, Any
import os
from openai import OpenAI as OpenAIClient

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


class QuizGenerator:
    def __init__(self, openai_api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL
        # Use OpenAI client with custom base URL for OpenRouter support
        self.client = OpenAIClient(
            api_key=self.openai_api_key,
            base_url=self.base_url
        ) if self.openai_api_key else None

    def generate(self, contexts: List[Dict[str, Any]], level: str = "Novice", topic: str = "") -> Dict[str, Any]:
        if not self.client:
            return {"level": level, "questions": [], "error": "OpenAI API key not configured"}
        
        # Extract context text
        context_texts = "\n\n".join([c.get("metadata", {}).get("text", "") for c in contexts[:5]])
        
        # Use topic if contexts are minimal
        subject = topic if topic and len(context_texts) < 50 else f"the following surgical topic: {context_texts}"
        
        # Create prompt for quiz generation
        prompt = f"""You are an educational surgical tutor creating a quiz for medical students.

Level: {level}
Topic: {subject}

Generate exactly 5 multiple-choice questions about {subject}. 
For {level} level:
- Novice: Focus on basic concepts, definitions, and fundamental procedures
- Intermediate: Include clinical reasoning and procedure steps
- Advanced: Cover complex scenarios, complications, and critical decision-making

Format your response as a JSON array with this structure:
[
  {{
    "id": 1,
    "question": "Question text here?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A) option1",
    "explanation": "Brief explanation of why this is correct"
  }}
]

IMPORTANT: The correct_answer must match EXACTLY one of the options including the letter prefix (e.g., "A) option1").
Return ONLY the JSON array, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            quiz_text = response.choices[0].message.content
            print(f"📝 GPT-4o raw response:\n{quiz_text}\n")
            
            # Try to parse as JSON
            import json
            try:
                # Clean the response - remove markdown code blocks if present
                cleaned_text = quiz_text.strip()
                if cleaned_text.startswith("```"):
                    # Remove code block markers
                    lines = cleaned_text.split('\n')
                    cleaned_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_text
                    cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
                
                print(f"🧹 Cleaned JSON:\n{cleaned_text}\n")
                questions = json.loads(cleaned_text)
                print(f"✅ Parsed {len(questions)} questions successfully")
                return {"level": level, "questions": questions}
            except json.JSONDecodeError as je:
                print(f"❌ JSON parsing failed: {je}")
                print(f"Failed text: {quiz_text[:500]}")
                # If JSON parsing fails, return the raw text
                return {"level": level, "quiz_text": quiz_text, "questions": [], "error": f"JSON parse error: {str(je)}"}
                
        except Exception as e:
            print(f"❌ Quiz generation exception: {e}")
            return {"level": level, "questions": [], "error": f"Failed to generate quiz: {str(e)}"}
