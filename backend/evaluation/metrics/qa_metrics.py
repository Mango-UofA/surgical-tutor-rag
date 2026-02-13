"""
QA Metrics for RAG System Evaluation
Implements Exact Match, F1, BLEU, ROUGE, BERTScore
"""

import re
import string
from typing import List, Dict
from collections import Counter
import numpy as np


class QAMetrics:
    """Calculate QA evaluation metrics"""
    
    @staticmethod
    def normalize_answer(text: str) -> str:
        """Normalize text for comparison (lowercase, remove punctuation/articles)"""
        # Handle dict input (from generator that returns dict with 'answer' key)
        if isinstance(text, dict):
            text = text.get('answer', str(text))
        
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
        
        # Lowercase
        text = text.lower()
        
        # Remove punctuation
        text = ''.join(ch if ch not in string.punctuation else ' ' for ch in text)
        
        # Remove articles
        text = re.sub(r'\b(a|an|the)\b', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def exact_match(prediction: str, reference: str) -> float:
        """
        Exact Match: 1 if normalized strings match exactly, 0 otherwise
        
        Args:
            prediction: Model's generated answer
            reference: Ground truth answer
            
        Returns:
            EM score (0 or 1)
        """
        pred_norm = QAMetrics.normalize_answer(prediction)
        ref_norm = QAMetrics.normalize_answer(reference)
        
        return 1.0 if pred_norm == ref_norm else 0.0
    
    @staticmethod
    def f1_score(prediction: str, reference: str) -> float:
        """
        Token-level F1 score
        
        Args:
            prediction: Model's generated answer
            reference: Ground truth answer
            
        Returns:
            F1 score (0-1)
        """
        pred_tokens = QAMetrics.normalize_answer(prediction).split()
        ref_tokens = QAMetrics.normalize_answer(reference).split()
        
        if len(pred_tokens) == 0 or len(ref_tokens) == 0:
            return 0.0
        
        common = Counter(pred_tokens) & Counter(ref_tokens)
        num_common = sum(common.values())
        
        if num_common == 0:
            return 0.0
        
        precision = num_common / len(pred_tokens)
        recall = num_common / len(ref_tokens)
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1
    
    @staticmethod
    def bleu_score(prediction: str, reference: str, max_n: int = 4) -> float:
        """
        BLEU score with geometric mean of n-gram precisions
        
        Args:
            prediction: Model's generated answer
            reference: Ground truth answer
            max_n: Maximum n-gram size (default: 4)
            
        Returns:
            BLEU score (0-1)
        """
        pred_tokens = QAMetrics.normalize_answer(prediction).split()
        ref_tokens = QAMetrics.normalize_answer(reference).split()
        
        if len(pred_tokens) == 0:
            return 0.0
        
        # Calculate n-gram precisions
        precisions = []
        for n in range(1, max_n + 1):
            pred_ngrams = [tuple(pred_tokens[i:i+n]) for i in range(len(pred_tokens) - n + 1)]
            ref_ngrams = [tuple(ref_tokens[i:i+n]) for i in range(len(ref_tokens) - n + 1)]
            
            if len(pred_ngrams) == 0:
                break
            
            common = Counter(pred_ngrams) & Counter(ref_ngrams)
            num_common = sum(common.values())
            
            precision = num_common / len(pred_ngrams) if len(pred_ngrams) > 0 else 0
            precisions.append(precision)
        
        if not precisions or all(p == 0 for p in precisions):
            return 0.0
        
        # Geometric mean
        bleu = np.exp(np.mean([np.log(p) if p > 0 else -np.inf for p in precisions]))
        
        # Brevity penalty
        bp = 1.0
        if len(pred_tokens) < len(ref_tokens):
            bp = np.exp(1 - len(ref_tokens) / len(pred_tokens))
        
        return bp * bleu
    
    @staticmethod
    def rouge_l(prediction: str, reference: str) -> float:
        """
        ROUGE-L: F1 based on Longest Common Subsequence
        
        Args:
            prediction: Model's generated answer
            reference: Ground truth answer
            
        Returns:
            ROUGE-L F1 score (0-1)
        """
        pred_tokens = QAMetrics.normalize_answer(prediction).split()
        ref_tokens = QAMetrics.normalize_answer(reference).split()
        
        if len(pred_tokens) == 0 or len(ref_tokens) == 0:
            return 0.0
        
        # LCS dynamic programming
        m, n = len(pred_tokens), len(ref_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if pred_tokens[i-1] == ref_tokens[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        
        if lcs_length == 0:
            return 0.0
        
        precision = lcs_length / len(pred_tokens)
        recall = lcs_length / len(ref_tokens)
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1


def evaluate_qa(
    predictions: List[Dict],
    include_bleu: bool = True,
    include_rouge: bool = True
) -> Dict[str, float]:
    """
    Evaluate QA performance across multiple predictions
    
    Args:
        predictions: List of dicts with 'prediction', 'reference' keys
        include_bleu: Whether to calculate BLEU (slower)
        include_rouge: Whether to calculate ROUGE (slower)
        
    Returns:
        Dict of metric names to average scores
    """
    metrics_obj = QAMetrics()
    results = {
        'exact_match': [],
        'f1': []
    }
    
    if include_bleu:
        results['bleu'] = []
    if include_rouge:
        results['rouge_l'] = []
    
    for item in predictions:
        pred = item['prediction']
        ref = item['reference']
        
        results['exact_match'].append(metrics_obj.exact_match(pred, ref))
        results['f1'].append(metrics_obj.f1_score(pred, ref))
        
        if include_bleu:
            results['bleu'].append(metrics_obj.bleu_score(pred, ref))
        if include_rouge:
            results['rouge_l'].append(metrics_obj.rouge_l(pred, ref))
    
    # Average across all predictions
    avg_results = {
        metric: np.mean(scores) for metric, scores in results.items()
    }
    
    return avg_results


def evaluate_multi_reference_qa(
    predictions: List[Dict]
) -> Dict[str, float]:
    """
    Evaluate QA with multiple reference answers per question
    
    Args:
        predictions: List of dicts with 'prediction', 'references' (list) keys
        
    Returns:
        Dict of metric names to average scores
    """
    metrics_obj = QAMetrics()
    results = {
        'exact_match': [],
        'f1': [],
        'bleu': [],
        'rouge_l': []
    }
    
    for item in predictions:
        pred = item['prediction']
        refs = item['references']  # List of acceptable answers
        
        # Take max score across all references
        em_scores = [metrics_obj.exact_match(pred, ref) for ref in refs]
        f1_scores = [metrics_obj.f1_score(pred, ref) for ref in refs]
        bleu_scores = [metrics_obj.bleu_score(pred, ref) for ref in refs]
        rouge_scores = [metrics_obj.rouge_l(pred, ref) for ref in refs]
        
        results['exact_match'].append(max(em_scores))
        results['f1'].append(max(f1_scores))
        results['bleu'].append(max(bleu_scores))
        results['rouge_l'].append(max(rouge_scores))
    
    # Average across all predictions
    avg_results = {
        metric: np.mean(scores) for metric, scores in results.items()
    }
    
    return avg_results


if __name__ == "__main__":
    # Example usage
    test_predictions = [
        {
            'prediction': 'Pneumothorax and arterial puncture are common complications.',
            'reference': 'Common complications include pneumothorax and arterial puncture.'
        },
        {
            'prediction': 'The appendix is located in the right lower quadrant.',
            'reference': 'The appendix is in the right lower quadrant of the abdomen.'
        }
    ]
    
    results = evaluate_qa(test_predictions)
    print("QA Metrics:")
    for metric, score in results.items():
        print(f"  {metric}: {score:.4f}")
