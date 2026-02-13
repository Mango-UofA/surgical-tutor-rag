"""
Hallucination Detection and Faithfulness Metrics
Measures if generated answers are grounded in retrieved context
"""

import re
from typing import List, Dict, Tuple
import numpy as np


class HallucinationDetector:
    """Detect hallucinations in RAG-generated answers"""
    
    def __init__(self, openrouter_api_key: str = None):
        """
        Initialize hallucination detector
        
        Args:
            openrouter_api_key: API key for LLM-based evaluation
        """
        self.api_key = openrouter_api_key
    
    @staticmethod
    def _to_string(text) -> str:
        """Convert input to string, handling dict with 'answer' or 'text' keys"""
        if isinstance(text, dict):
            return text.get('answer', text.get('text', str(text)))
        return str(text)
    
    def extract_claims(self, text: str) -> List[str]:
        """
        Extract individual factual claims from text
        Simple sentence-based extraction (can be improved with dependency parsing)
        
        Args:
            text: Answer text
            
        Returns:
            List of claim strings
        """
        text = self._to_string(text)
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims
    
    def lexical_overlap_score(self, answer: str, context: str) -> float:
        """
        Simple lexical overlap between answer and context
        
        Args:
            answer: Generated answer (str or dict with 'answer' key)
            context: Retrieved context chunks
            
        Returns:
            Overlap score (0-1)
        """
        # Convert to string
        answer = self._to_string(answer)
        context = self._to_string(context)
        
        # Normalize text
        answer_tokens = set(answer.lower().split())
        context_tokens = set(context.lower().split())
        
        if len(answer_tokens) == 0:
            return 0.0
        
        overlap = len(answer_tokens & context_tokens)
        return overlap / len(answer_tokens)
    
    def citation_coverage(self, answer: str, context_chunks: List[str]) -> Dict[str, float]:
        """
        Check if answer content can be attributed to context chunks
        
        Args:
            answer: Generated answer
            context_chunks: List of retrieved context strings
            
        Returns:
            Dict with coverage metrics
        """
        claims = self.extract_claims(answer)
        
        if not claims:
            return {
                'num_claims': 0,
                'supported_claims': 0,
                'coverage_ratio': 0.0
            }
        
        supported = 0
        for claim in claims:
            claim_tokens = set(claim.lower().split())
            
            # Check if majority of claim tokens appear in any context chunk
            for chunk in context_chunks:
                chunk_tokens = set(chunk.lower().split())
                overlap = len(claim_tokens & chunk_tokens)
                
                # If >70% of claim tokens in chunk, consider supported
                if overlap / len(claim_tokens) > 0.7:
                    supported += 1
                    break
        
        return {
            'num_claims': len(claims),
            'supported_claims': supported,
            'coverage_ratio': supported / len(claims)
        }
    
    async def nli_faithfulness_score(
        self,
        answer: str,
        context: str,
        model: str = "meta-llama/llama-3.1-8b-instruct:free"
    ) -> float:
        """
        Use LLM to check if answer is entailed by context (NLI-based)
        
        Args:
            answer: Generated answer
            context: Retrieved context
            model: LLM model for NLI
            
        Returns:
            Faithfulness score (0-1)
        """
        if not self.api_key:
            raise ValueError("API key required for NLI-based evaluation")
        
        import aiohttp
        
        prompt = f"""Task: Determine if the ANSWER is fully supported by the CONTEXT.
Respond with ONLY a number between 0 and 1:
- 1.0 = Answer is completely supported by context
- 0.5 = Answer is partially supported
- 0.0 = Answer contains information not in context (hallucination)

CONTEXT:
{context}

ANSWER:
{answer}

FAITHFULNESS SCORE (0-1):"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 10
                }
            ) as resp:
                result = await resp.json()
                score_text = result['choices'][0]['message']['content'].strip()
                
                # Extract number from response
                try:
                    score = float(re.search(r'(\d+\.?\d*)', score_text).group(1))
                    return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]
                except:
                    return 0.5  # Default if parsing fails


def evaluate_hallucination(
    predictions: List[Dict],
    use_nli: bool = False,
    api_key: str = None
) -> Dict[str, float]:
    """
    Evaluate hallucination metrics across predictions
    
    Args:
        predictions: List of dicts with 'answer', 'context_chunks' keys
        use_nli: Whether to use LLM-based NLI (slower, more accurate)
        api_key: API key for NLI evaluation
        
    Returns:
        Dict of metric names to average scores
    """
    detector = HallucinationDetector(api_key)
    
    lexical_scores = []
    coverage_ratios = []
    nli_scores = []
    
    for item in predictions:
        answer = item['answer']
        context_chunks = item['context_chunks']
        context_text = ' '.join(context_chunks)
        
        # Lexical overlap
        lexical_scores.append(
            detector.lexical_overlap_score(answer, context_text)
        )
        
        # Citation coverage
        coverage = detector.citation_coverage(answer, context_chunks)
        coverage_ratios.append(coverage['coverage_ratio'])
        
        # NLI-based (optional, requires async)
        if use_nli:
            # Note: This is synchronous version, real implementation should use async
            # nli_scores.append(await detector.nli_faithfulness_score(answer, context_text))
            pass
    
    results = {
        'lexical_overlap': np.mean(lexical_scores),
        'citation_coverage': np.mean(coverage_ratios),
        'hallucination_rate': 1.0 - np.mean(coverage_ratios)  # Inverse of coverage
    }
    
    if use_nli and nli_scores:
        results['nli_faithfulness'] = np.mean(nli_scores)
    
    return results


def compare_hallucination_rates(
    rag_predictions: List[Dict],
    baseline_predictions: List[Dict],
    api_key: str = None
) -> Dict[str, Dict[str, float]]:
    """
    Compare hallucination rates between RAG system and baseline
    
    Args:
        rag_predictions: Predictions from RAG system
        baseline_predictions: Predictions from baseline (e.g., GPT-4o alone)
        api_key: API key for evaluation
        
    Returns:
        Dict with 'rag' and 'baseline' metrics
    """
    rag_metrics = evaluate_hallucination(rag_predictions, api_key=api_key)
    baseline_metrics = evaluate_hallucination(baseline_predictions, api_key=api_key)
    
    improvement = {
        metric: rag_metrics[metric] - baseline_metrics[metric]
        for metric in rag_metrics.keys()
    }
    
    return {
        'rag': rag_metrics,
        'baseline': baseline_metrics,
        'improvement': improvement
    }


if __name__ == "__main__":
    # Example usage
    test_data = [
        {
            'answer': 'Pneumothorax occurs in 1-3% of central line insertions according to the guidelines.',
            'context_chunks': [
                'Central venous catheter insertion has several complications. Pneumothorax is reported in 1-3% of cases.',
                'Other complications include arterial puncture and infection.'
            ]
        },
        {
            'answer': 'The appendix is always located in the lower right quadrant and is 10cm long.',
            'context_chunks': [
                'The appendix is typically found in the right lower quadrant.',
                'Appendicitis is inflammation of the appendix.'
            ]
        }
    ]
    
    results = evaluate_hallucination(test_data)
    print("Hallucination Metrics:")
    for metric, score in results.items():
        print(f"  {metric}: {score:.4f}")
