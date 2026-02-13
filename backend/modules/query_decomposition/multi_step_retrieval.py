"""
Multi-Step Query Decomposition for Complex Surgical Questions
Breaks complex queries into sequential sub-queries for comprehensive retrieval.

Novel contribution for MICCAI: First query decomposition system specifically 
designed for multi-faceted surgical questions with sequential reasoning.
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI as OpenAIClient
import os
import json
import logging

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """
    Decomposes complex surgical queries into simpler sub-queries.
    
    Examples:
    - "What are the steps, instruments, and complications of laparoscopic appendectomy?"
      → ["What are the main steps of laparoscopic appendectomy?",
         "What instruments are used in laparoscopic appendectomy?",
         "What are the common complications of laparoscopic appendectomy?"]
    
    - "How does the approach differ between pediatric and adult cholecystectomy?"
      → ["What is the standard approach for pediatric cholecystectomy?",
         "What is the standard approach for adult cholecystectomy?",
         "What are the key differences between pediatric and adult approaches?"]
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None):
        """
        Initialize query decomposer.
        
        Args:
            api_key: OpenAI API key
            base_url: API base URL
            model: Model name (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        
        self.client = OpenAIClient(
            api_key=self.api_key,
            base_url=self.base_url
        ) if self.api_key else None
        
        # Cache for decompositions
        self.decomposition_cache = {}
    
    def decompose_query(self, query: str, max_subqueries: int = 4) -> Dict[str, Any]:
        """
        Decompose a complex query into sub-queries.
        
        Args:
            query: Original complex query
            max_subqueries: Maximum number of sub-queries to generate
        
        Returns:
            Dictionary with:
            - is_complex: bool (whether decomposition is beneficial)
            - subqueries: List[str] (ordered sub-queries)
            - original_query: str
            - reasoning: str (why this decomposition)
        """
        # Check cache
        if query in self.decomposition_cache:
            logger.info("Using cached decomposition")
            return self.decomposition_cache[query]
        
        if not self.client:
            logger.warning("OpenAI client not configured, skipping decomposition")
            return self._no_decomposition_result(query)
        
        # Analyze query complexity
        complexity_analysis = self._analyze_query_complexity(query)
        
        # If simple query, don't decompose
        if not complexity_analysis['is_complex']:
            result = self._no_decomposition_result(query)
            self.decomposition_cache[query] = result
            return result
        
        # Perform decomposition
        try:
            decomposition_prompt = self._build_decomposition_prompt(query, max_subqueries)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at breaking down complex surgical questions into clear, sequential sub-questions. Return only valid JSON."},
                    {"role": "user", "content": decomposition_prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            result = json.loads(result_json)
            
            # Validate and format
            formatted_result = {
                'is_complex': True,
                'subqueries': result.get('subqueries', [query]),
                'original_query': query,
                'reasoning': result.get('reasoning', 'Query decomposed for comprehensive retrieval'),
                'complexity_score': complexity_analysis['complexity_score']
            }
            
            # Limit subqueries
            formatted_result['subqueries'] = formatted_result['subqueries'][:max_subqueries]
            
            # Cache result
            self.decomposition_cache[query] = formatted_result
            
            logger.info(f"Decomposed into {len(formatted_result['subqueries'])} sub-queries")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Decom position failed: {e}")
            result = self._no_decomposition_result(query)
            return result
    
    def _analyze_query_complexity(self, query: str) -> Dict[str, bool]:
        """
        Analyze if query is complex enough to benefit from decomposition.
        
        Complexity indicators:
        - Multiple questions (and, or, also)
        - Comparison queries (differ, compare, versus)
        - Multi-aspect queries (steps AND instruments AND complications)
        - Long queries (>100 chars)
        """
        query_lower = query.lower()
        
        complexity_score = 0
        
        # Multiple question words
        question_words = ['what', 'how', 'why', 'when', 'which', 'where']
        question_count = sum(1 for word in question_words if query_lower.count(word) > 0)
        if question_count > 1:
            complexity_score += 2
        
        # Conjunction indicators
        conjunctions = [' and ', ' or ', ' also ', ', and', ', or']
        if any(conj in query_lower for conj in conjunctions):
            complexity_score += 2
        
        # Comparison indicators
        comparisons = ['differ', 'compare', 'versus', 'vs', 'difference between', 'contrast']
        if any(comp in query_lower for comp in comparisons):
            complexity_score += 3
        
        # Multi-aspect indicators
        aspects = ['step', 'instrument', 'complication', 'indication', 'contraindication', 'technique']
        aspect_count = sum(1 for aspect in aspects if aspect in query_lower)
        if aspect_count >= 2:
            complexity_score += 2
        
        # Length indicator
        if len(query) > 100:
            complexity_score += 1
        
        # Decision: complex if score >= 3
        is_complex = complexity_score >= 3
        
        return {
            'is_complex': is_complex,
            'complexity_score': complexity_score,
            'indicators': {
                'multiple_questions': question_count > 1,
                'has_conjunctions': any(conj in query_lower for conj in conjunctions),
                'is_comparison': any(comp in query_lower for comp in comparisons),
                'multi_aspect': aspect_count >= 2,
                'long_query': len(query) > 100
            }
        }
    
    def _build_decomposition_prompt(self, query: str, max_subqueries: int) -> str:
        """Build prompt for query decomposition."""
        return f"""Decompose this complex surgical question into {max_subqueries} or fewer sequential sub-questions.

Original question: {query}

Requirements:
1. Each sub-question should be self-contained and answerable independently
2. Sub-questions should cover all aspects of the original question
3. Order sub-questions logically (foundational concepts first)
4. Keep sub-questions focused and specific
5. Use clear surgical terminology

Return ONLY valid JSON in this exact format:
{{
    "subqueries": [
        "First specific sub-question...",
        "Second specific sub-question...",
        "Third specific sub-question..."
    ],
    "reasoning": "Brief explanation of decomposition strategy"
}}

Examples:

Original: "What are the steps, instruments, and complications of laparoscopic appendectomy?"
{{
    "subqueries": [
        "What are the main procedural steps of laparoscopic appendectomy?",
        "What surgical instruments are used in laparoscopic appendectomy?",
        "What are the common complications of laparoscopic appendectomy?"
    ],
    "reasoning": "Decomposed into three aspect-specific questions covering procedure, tools, and safety"
}}

Original: "How does the surgical approach differ between pediatric and adult laparoscopic cholecystectomy?"
{{
    "subqueries": [
        "What is the standard surgical approach for pediatric laparoscopic cholecystectomy?",
        "What is the standard surgical approach for adult laparoscopic cholecystectomy?",
        "What are the key anatomical and technical differences between pediatric and adult cholecystectomy?"
    ],
    "reasoning": "Decomposed comparison into separate queries for each population plus explicit difference analysis"
}}
"""
    
    def _no_decomposition_result(self, query: str) -> Dict[str, Any]:
        """Return result indicating no decomposition needed."""
        return {
            'is_complex': False,
            'subqueries': [query],
            'original_query': query,
            'reasoning': 'Query is sufficiently simple and focused',
            'complexity_score': 0
        }
    
    def clear_cache(self):
        """Clear decomposition cache."""
        self.decomposition_cache = {}
        logger.info("Decomposition cache cleared")


class MultiStepRetriever:
    """
    Retrieves documents using multi-step query decomposition.
    
    Workflow:
    1. Decompose complex query
    2. Retrieve for each sub-query
    3. Aggregate and deduplicate results
    4. Re-rank by relevance to original query
    """
    
    def __init__(self,
                 base_retriever,  # FaissManager or GraphEnhancedRetriever
                 query_decomposer: QueryDecomposer,
                 use_decomposition: bool = True):
        """
        Initialize multi-step retriever.
        
        Args:
            base_retriever: Base retrieval system (FAISS or Graph)
            query_decomposer: Query decomposition system
            use_decomposition: Whether to use decomposition (disable for baseline)
        """
        self.base_retriever = base_retriever
        self.decomposer = query_decomposer
        self.use_decomposition = use_decomposition
        
        logger.info(f"Multi-step retriever initialized (decomposition: {use_decomposition})")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents with optional query decomposition.
        
        Args:
            query: User query
            top_k: Number of results to return
        
        Returns:
            Retrieved documents with scores
        """
        if not self.use_decomposition:
            # Baseline: direct retrieval
            return self._retrieve_single(query, top_k)
        
        # Decompose query
        decomposition_result = self.decomposer.decompose_query(query)
        
        if not decomposition_result['is_complex']:
            # Simple query: direct retrieval
            return self._retrieve_single(query, top_k)
        
        # Complex query: multi-step retrieval
        subqueries = decomposition_result['subqueries']
        logger.info(f"Retrieving for {len(subqueries)} sub-queries")
        
        # Retrieve for each sub-query
        all_results = []
        for i, subquery in enumerate(subqueries):
            logger.info(f"Sub-query {i+1}/{len(subqueries)}: {subquery[:60]}...")
            
            # Retrieve more candidates per sub-query
            subquery_results = self._retrieve_single(subquery, top_k * 2)
            
            # Tag with sub-query info
            for result in subquery_results:
                result['subquery_index'] = i
                result['subquery'] = subquery
            
            all_results.extend(subquery_results)
        
        # Deduplicate and re-rank
        final_results = self._aggregate_results(all_results, query, top_k)
        
        return final_results
    
    def _retrieve_single(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform single retrieval using base retriever."""
        try:
            # Check if base retriever is GraphEnhancedRetriever
            if hasattr(self.base_retriever, 'retrieve'):
                # GraphEnhancedRetriever
                results = self.base_retriever.retrieve(query, top_k=top_k)
            elif hasattr(self.base_retriever, 'query'):
                # FaissManager
                from ..embedder.embedder import BioClinicalEmbedder
                embedder = BioClinicalEmbedder('emilyalsentzer/Bio_ClinicalBERT')
                query_emb = embedder.embed_texts([query])[0]
                results = self.base_retriever.query(query_emb, top_k=top_k)
            else:
                logger.error("Base retriever has unknown interface")
                return []
            
            return results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def _aggregate_results(self, 
                          all_results: List[Dict[str, Any]],
                          original_query: str,
                          top_k: int) -> List[Dict[str, Any]]:
        """
        Aggregate results from multiple sub-queries.
        
        Strategy:
        1. Deduplicate by text content
        2. Boost scores for chunks appearing in multiple sub-query results
        3. Re-rank by relevance to original query
        """
        # Deduplicate by text
        seen_texts = set()
        unique_results = []
        
        for result in all_results:
            text = result.get('text', '')[:500]  # Use first 500 chars for dedup
            if text not in seen_texts and text:
                seen_texts.add(text)
                result['subquery_count'] = 1
                unique_results.append(result)
            else:
                # Already seen: increment count
                for existing in unique_results:
                    if existing.get('text', '')[:500] == text:
                        existing['subquery_count'] = existing.get('subquery_count', 1) + 1
                        break
        
        # Boost scores for chunks appearing in multiple sub-queries
        for result in unique_results:
            base_score = result.get('score', 0.5)
            subquery_boost = min(0.3, result.get('subquery_count', 1) * 0.1)
            result['final_score'] = base_score + subquery_boost
        
        # Sort by final score
        unique_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return unique_results[:top_k]
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about multi-step retrieval."""
        return {
            'decomposition_enabled': self.use_decomposition,
            'cache_size': len(self.decomposer.decomposition_cache),
            'base_retriever_type': type(self.base_retriever).__name__
        }
