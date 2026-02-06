"""
Semantic Similarity Metrics for QA Evaluation
Uses sentence transformers for better semantic matching beyond exact text overlap
"""

import numpy as np
from typing import List, Dict
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")


class SemanticMetrics:
    """Calculate semantic similarity metrics"""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """
        Initialize semantic metrics calculator
        
        Args:
            model_name: HuggingFace model name for sentence embeddings
        """
        if HAS_SEMANTIC:
            try:
                self.model = SentenceTransformer(model_name)
                self.available = True
            except Exception as e:
                print(f"⚠️  Could not load semantic model: {e}")
                self.model = None
                self.available = False
        else:
            self.model = None
            self.available = False
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not self.available or not text1 or not text2:
            return 0.0
        
        try:
            embeddings = self.model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def answer_equivalence(self, prediction: str, reference: str, threshold: float = 0.7) -> float:
        """
        Check if prediction is semantically equivalent to reference
        
        Args:
            prediction: Generated answer
            reference: Ground truth answer
            threshold: Similarity threshold for equivalence
            
        Returns:
            1.0 if equivalent, else 0.0
        """
        similarity = self.semantic_similarity(prediction, reference)
        return 1.0 if similarity >= threshold else 0.0
    
    def multi_reference_similarity(self, prediction: str, references: List[str]) -> float:
        """
        Calculate maximum similarity to multiple reference answers
        
        Args:
            prediction: Generated answer
            references: List of acceptable reference answers
            
        Returns:
            Maximum similarity score
        """
        if not references:
            return 0.0
        
        similarities = [self.semantic_similarity(prediction, ref) for ref in references]
        return max(similarities)


def evaluate_semantic_similarity(predictions: List[Dict], model_name: str = 'all-MiniLM-L6-v2') -> Dict[str, float]:
    """
    Evaluate semantic similarity for a batch of predictions
    
    Args:
        predictions: List of dicts with 'prediction' and 'reference' keys
        model_name: Sentence transformer model name
        
    Returns:
        Dict of metric names to scores
    """
    metrics = SemanticMetrics(model_name)
    
    if not metrics.available:
        print("⚠️  Semantic metrics not available. Returning zeros.")
        return {
            'semantic_similarity': 0.0,
            'semantic_equivalence_70': 0.0,
            'semantic_equivalence_80': 0.0,
            'semantic_equivalence_90': 0.0
        }
    
    similarities = []
    equiv_70 = []
    equiv_80 = []
    equiv_90 = []
    
    for pred in predictions:
        prediction = pred['prediction']
        reference = pred['reference']
        
        # Calculate similarity
        sim = metrics.semantic_similarity(prediction, reference)
        similarities.append(sim)
        
        # Check equivalence at different thresholds
        equiv_70.append(1.0 if sim >= 0.70 else 0.0)
        equiv_80.append(1.0 if sim >= 0.80 else 0.0)
        equiv_90.append(1.0 if sim >= 0.90 else 0.0)
    
    return {
        'semantic_similarity': np.mean(similarities),
        'semantic_equivalence_70': np.mean(equiv_70),
        'semantic_equivalence_80': np.mean(equiv_80),
        'semantic_equivalence_90': np.mean(equiv_90)
    }


def calculate_answer_faithfulness(answer: str, contexts: List[str], model_name: str = 'all-MiniLM-L6-v2') -> float:
    """
    Calculate how faithful the answer is to retrieved contexts
    
    Args:
        answer: Generated answer
        contexts: Retrieved context chunks
        model_name: Sentence transformer model name
        
    Returns:
        Maximum similarity to any context (0-1)
    """
    metrics = SemanticMetrics(model_name)
    
    if not metrics.available or not contexts:
        return 0.0
    
    # Calculate similarity to each context
    similarities = [metrics.semantic_similarity(answer, ctx) for ctx in contexts]
    
    # Return maximum (best match)
    return max(similarities) if similarities else 0.0


if __name__ == "__main__":
    # Example usage
    print("Testing Semantic Metrics...")
    
    test_predictions = [
        {
            'prediction': 'The procedure typically takes 30 to 45 minutes to complete.',
            'reference': 'Typical operating time is 30-45 minutes.'
        },
        {
            'prediction': 'Ultrasound guidance decreases complication rates by half.',
            'reference': 'Ultrasound guidance reduces complications by 50%.'
        }
    ]
    
    results = evaluate_semantic_similarity(test_predictions)
    
    print("\nSemantic Similarity Results:")
    for metric, score in results.items():
        print(f"  {metric}: {score:.4f}")
