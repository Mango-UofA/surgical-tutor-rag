"""
Retrieval Metrics for RAG System Evaluation
Implements standard IR metrics: Recall@K, MRR, NDCG, MAP
"""

import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict


class RetrievalMetrics:
    """Calculate standard information retrieval metrics"""
    
    @staticmethod
    def recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
        """
        Recall@K: Proportion of relevant documents in top-K results
        
        Args:
            retrieved_ids: Ordered list of retrieved document IDs
            relevant_ids: List of ground truth relevant document IDs
            k: Number of top results to consider
            
        Returns:
            Recall@K score (0-1)
        """
        if not relevant_ids:
            return 0.0
            
        retrieved_at_k = set(retrieved_ids[:k])
        relevant_set = set(relevant_ids)
        
        hits = len(retrieved_at_k & relevant_set)
        return hits / len(relevant_set)
    
    @staticmethod
    def precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
        """
        Precision@K: Proportion of relevant documents among top-K results
        """
        if k == 0:
            return 0.0
            
        retrieved_at_k = set(retrieved_ids[:k])
        relevant_set = set(relevant_ids)
        
        hits = len(retrieved_at_k & relevant_set)
        return hits / k
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """
        MRR: Reciprocal rank of the first relevant document
        
        Args:
            retrieved_ids: Ordered list of retrieved document IDs
            relevant_ids: List of ground truth relevant document IDs
            
        Returns:
            MRR score (0-1)
        """
        relevant_set = set(relevant_ids)
        
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain at K
        
        Args:
            retrieved_ids: Ordered list of retrieved document IDs
            relevant_ids: List of ground truth relevant document IDs
            k: Number of top results to consider
            
        Returns:
            NDCG@K score (0-1)
        """
        relevant_set = set(relevant_ids)
        
        # DCG: Discounted Cumulative Gain
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved_ids[:k], 1):
            relevance = 1 if doc_id in relevant_set else 0
            dcg += relevance / np.log2(rank + 1)
        
        # IDCG: Ideal DCG (all relevant docs at top)
        idcg = 0.0
        for rank in range(1, min(len(relevant_ids), k) + 1):
            idcg += 1.0 / np.log2(rank + 1)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def average_precision(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """
        Average Precision: Mean precision at each relevant document position
        
        Args:
            retrieved_ids: Ordered list of retrieved document IDs
            relevant_ids: List of ground truth relevant document IDs
            
        Returns:
            AP score (0-1)
        """
        if not relevant_ids:
            return 0.0
            
        relevant_set = set(relevant_ids)
        precision_sum = 0.0
        num_relevant_found = 0
        
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                num_relevant_found += 1
                precision_at_rank = num_relevant_found / rank
                precision_sum += precision_at_rank
        
        if num_relevant_found == 0:
            return 0.0
        
        return precision_sum / len(relevant_set)


def evaluate_retrieval(
    queries: List[Dict],
    retrieval_function,
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, float]:
    """
    Evaluate retrieval performance across multiple queries
    
    Args:
        queries: List of dicts with 'query', 'relevant_doc_ids' keys
        retrieval_function: Function that takes query and returns ordered list of doc IDs
        k_values: List of K values to evaluate
        
    Returns:
        Dict of metric names to average scores
    """
    metrics = RetrievalMetrics()
    results = defaultdict(list)
    
    for query_data in queries:
        query = query_data['query']
        relevant_ids = query_data['relevant_doc_ids']
        
        # Get retrieved documents
        retrieved_ids = retrieval_function(query)
        
        # Calculate metrics
        for k in k_values:
            results[f'Recall@{k}'].append(
                metrics.recall_at_k(retrieved_ids, relevant_ids, k)
            )
            results[f'Precision@{k}'].append(
                metrics.precision_at_k(retrieved_ids, relevant_ids, k)
            )
            results[f'NDCG@{k}'].append(
                metrics.ndcg_at_k(retrieved_ids, relevant_ids, k)
            )
        
        results['MRR'].append(
            metrics.mean_reciprocal_rank(retrieved_ids, relevant_ids)
        )
        results['MAP'].append(
            metrics.average_precision(retrieved_ids, relevant_ids)
        )
    
    # Average across all queries
    avg_results = {
        metric: np.mean(scores) for metric, scores in results.items()
    }
    
    return avg_results


if __name__ == "__main__":
    # Example usage
    test_queries = [
        {
            'query': 'complications of appendectomy',
            'relevant_doc_ids': ['doc_1', 'doc_5', 'doc_12']
        }
    ]
    
    def dummy_retrieval(query):
        return ['doc_1', 'doc_3', 'doc_5', 'doc_7', 'doc_9']
    
    results = evaluate_retrieval(test_queries, dummy_retrieval)
    print("Retrieval Metrics:")
    for metric, score in results.items():
        print(f"  {metric}: {score:.4f}")
