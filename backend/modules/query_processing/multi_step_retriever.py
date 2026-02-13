"""
Multi-Step Retrieval Manager
Coordinates retrieval across multiple sub-queries and merges results.
"""

from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class MultiStepRetriever:
    """
    Manages retrieval across multiple decomposed sub-queries.
    
    Process:
    1. Decompose complex query into sub-queries
    2. Retrieve independently for each sub-query
    3. Merge results with deduplication
    4. Tag chunks with source sub-query for context
    """
    
    def __init__(self, 
                 retriever,  # GraphEnhancedRetriever or FaissManager
                 query_decomposer,  # QueryDecomposer
                 use_decomposition: bool = True):
        """
        Initialize multi-step retriever.
        
        Args:
            retriever: Retriever instance (GraphEnhancedRetriever or FaissManager)
            query_decomposer: QueryDecomposer instance
            use_decomposition: Whether to use query decomposition
        """
        self.retriever = retriever
        self.decomposer = query_decomposer
        self.use_decomposition = use_decomposition
    
    def retrieve(self, 
                 query: str, 
                 top_k: int = 5,
                 top_k_per_subquery: int = 3,
                 **retriever_kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve with multi-step decomposition.
        
        Args:
            query: Original user query
            top_k: Total number of results to return
            top_k_per_subquery: Number of results per sub-query
            **retriever_kwargs: Additional arguments for retriever
        
        Returns:
            List of retrieved contexts with metadata
        """
        # Step 1: Decompose query
        if self.use_decomposition:
            subqueries = self.decomposer.decompose(query)
            logger.info(f"Query decomposed into {len(subqueries)} sub-queries")
        else:
            subqueries = [query]
            logger.info("Decomposition disabled, using original query")
        
        # If only one subquery, just do normal retrieval
        if len(subqueries) == 1:
            return self._single_retrieval(query, top_k, **retriever_kwargs)
        
        # Step 2: Retrieve for each sub-query
        all_results = []
        for idx, subquery in enumerate(subqueries):
            logger.info(f"Retrieving for sub-query {idx+1}/{len(subqueries)}: {subquery[:100]}")
            
            results = self._single_retrieval(subquery, top_k_per_subquery, **retriever_kwargs)
            
            # Tag results with sub-query index
            for result in results:
                result['subquery_idx'] = idx
                result['subquery'] = subquery
            
            all_results.extend(results)
        
        # Step 3: Deduplicate and merge
        merged_results = self._deduplicate_and_merge(all_results, top_k)
        
        logger.info(f"Multi-step retrieval complete: {len(merged_results)} unique results returned")
        
        return merged_results
    
    def _single_retrieval(self, 
                         query: str, 
                         top_k: int, 
                         **retriever_kwargs) -> List[Dict[str, Any]]:
        """
        Perform single retrieval operation.
        
        Args:
            query: Query string
            top_k: Number of results
            **retriever_kwargs: Additional retriever arguments
        
        Returns:
            List of retrieved contexts
        """
        try:
            # Handle different retriever types
            if hasattr(self.retriever, 'retrieve'):
                # GraphEnhancedRetriever
                return self.retriever.retrieve(query, top_k=top_k, **retriever_kwargs)
            elif hasattr(self.retriever, 'query'):
                # FaissManager - needs embedding
                if 'embedder' in retriever_kwargs:
                    embedder = retriever_kwargs.pop('embedder')
                    q_emb = embedder.embed_texts([query])[0]
                    return self.retriever.query(q_emb, top_k=top_k)
                else:
                    logger.error("FaissManager requires embedder in retriever_kwargs")
                    return []
            else:
                logger.error(f"Unknown retriever type: {type(self.retriever)}")
                return []
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query[:50]}': {e}")
            return []
    
    def _deduplicate_and_merge(self, 
                               results: List[Dict[str, Any]], 
                               top_k: int) -> List[Dict[str, Any]]:
        """
        Deduplicate results by chunk ID and merge scores.
        
        Strategy:
        - Group by chunk ID (or text if no ID)
        - Keep highest score for each chunk
        - Track which sub-queries retrieved each chunk
        - Return top_k results sorted by score
        
        Args:
            results: All retrieval results from sub-queries
            top_k: Number of results to return
        
        Returns:
            Deduplicated and merged results
        """
        # Group by chunk identifier
        chunk_map = defaultdict(lambda: {
            'scores': [],
            'subquery_indices': [],
            'subqueries': [],
            'first_result': None
        })
        
        for result in results:
            # Get chunk identifier
            chunk_id = self._get_chunk_id(result)
            
            # Store scores and sub-query info
            chunk_map[chunk_id]['scores'].append(result.get('score', 0.0))
            chunk_map[chunk_id]['subquery_indices'].append(result.get('subquery_idx', 0))
            chunk_map[chunk_id]['subqueries'].append(result.get('subquery', ''))
            
            # Store first occurrence
            if chunk_map[chunk_id]['first_result'] is None:
                chunk_map[chunk_id]['first_result'] = result
        
        # Create merged results
        merged = []
        for chunk_id, data in chunk_map.items():
            result = data['first_result'].copy()
            
            # Use highest score
            result['score'] = max(data['scores'])
            
            # Add multi-query metadata
            result['retrieved_by_subqueries'] = list(set(data['subquery_indices']))
            result['num_subqueries'] = len(set(data['subquery_indices']))
            result['all_subqueries'] = list(set(data['subqueries']))
            
            # Boost score slightly if retrieved by multiple sub-queries (relevance signal)
            if result['num_subqueries'] > 1:
                result['score'] *= (1.0 + 0.1 * (result['num_subqueries'] - 1))
            
            merged.append(result)
        
        # Sort by score and return top_k
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return merged[:top_k]
    
    def _get_chunk_id(self, result: Dict[str, Any]) -> str:
        """
        Extract a unique identifier for a chunk.
        
        Args:
            result: Retrieval result dictionary
        
        Returns:
            Unique identifier string
        """
        # Try various ID fields
        if 'id' in result:
            return str(result['id'])
        
        if 'chunk_id' in result:
            return str(result['chunk_id'])
        
        # Use metadata
        metadata = result.get('metadata', {})
        if 'id' in metadata:
            return str(metadata['id'])
        
        if 'chunk_id' in metadata:
            return str(metadata['chunk_id'])
        
        # Fallback: hash of text
        text = metadata.get('text', '')
        if text:
            return str(hash(text[:200]))  # Hash first 200 chars
        
        # Last resort: hash of entire result
        return str(hash(str(result)))
