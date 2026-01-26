"""
Graph-Enhanced Retriever
Combines vector-based FAISS retrieval with graph-based knowledge retrieval
to provide comprehensive and contextually rich results.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from ..retriever.faiss_manager import FAISSManager
from .neo4j_manager import Neo4jManager
from .entity_extractor import MedicalEntityExtractor

logger = logging.getLogger(__name__)


class GraphEnhancedRetriever:
    """
    Hybrid retrieval system that combines:
    1. Vector similarity search (FAISS) - finds semantically similar content
    2. Graph traversal (Neo4j) - finds structurally related knowledge
    3. Entity expansion - enriches results with related medical entities
    
    This provides more comprehensive and contextually aware retrieval
    compared to vector search alone.
    """
    
    def __init__(self, 
                 faiss_manager: FAISSManager,
                 neo4j_manager: Neo4jManager,
                 entity_extractor: MedicalEntityExtractor,
                 vector_weight: float = 0.6,
                 graph_weight: float = 0.4):
        """
        Initialize the hybrid retriever.
        
        Args:
            faiss_manager: FAISS vector store manager
            neo4j_manager: Neo4j graph database manager
            entity_extractor: Medical entity extraction system
            vector_weight: Weight for vector similarity scores (0-1)
            graph_weight: Weight for graph relevance scores (0-1)
        """
        self.faiss = faiss_manager
        self.graph = neo4j_manager
        self.extractor = entity_extractor
        
        # Ensure weights sum to 1
        total_weight = vector_weight + graph_weight
        self.vector_weight = vector_weight / total_weight
        self.graph_weight = graph_weight / total_weight
        
        logger.info(f"Initialized hybrid retriever (vector: {self.vector_weight:.2f}, graph: {self.graph_weight:.2f})")
    
    def retrieve(self, 
                 query: str, 
                 top_k: int = 5,
                 use_graph: bool = True,
                 expand_entities: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using hybrid approach.
        
        Args:
            query: User query
            top_k: Number of results to return
            use_graph: Whether to use graph-based retrieval
            expand_entities: Whether to expand results with graph context
        
        Returns:
            List of retrieved documents with scores and metadata
        """
        # Step 1: Vector-based retrieval
        vector_results = self._vector_retrieve(query, top_k * 2)  # Get more candidates
        
        if not use_graph:
            return vector_results[:top_k]
        
        # Step 2: Extract entities from query
        query_entities = self.extractor.extract_entities(query)
        
        # Step 3: Graph-based retrieval
        graph_results = self._graph_retrieve(query_entities, top_k)
        
        # Step 4: Merge and re-rank results
        merged_results = self._merge_results(vector_results, graph_results, top_k)
        
        # Step 5: Optionally expand with graph context
        if expand_entities:
            merged_results = self._expand_with_graph_context(merged_results)
        
        return merged_results
    
    def _vector_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Perform vector-based retrieval using FAISS.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of documents with vector similarity scores
        """
        try:
            results = self.faiss.search(query, top_k=top_k)
            
            # Add retrieval source
            for result in results:
                result['retrieval_source'] = 'vector'
                result['vector_score'] = result.get('score', 0.0)
            
            return results
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return []
    
    def _graph_retrieve(self, entities: Dict[str, List[str]], top_k: int) -> List[Dict[str, Any]]:
        """
        Perform graph-based retrieval using extracted entities.
        
        Args:
            entities: Extracted entities from query
            top_k: Number of results
        
        Returns:
            List of graph-based results
        """
        graph_results = []
        
        # Extract main procedures from query
        procedures = entities.get('procedures', [])
        
        for procedure in procedures[:3]:  # Limit to top 3 procedures
            try:
                # Get comprehensive procedure context
                context = self.graph.get_procedure_context(procedure)
                
                if context:
                    graph_results.append({
                        'text': self._format_graph_context(context),
                        'metadata': {
                            'source': 'knowledge_graph',
                            'procedure': procedure,
                            'entities': context
                        },
                        'retrieval_source': 'graph',
                        'graph_score': 1.0  # Max relevance for exact procedure match
                    })
                
                # Also get related procedures
                related = self.graph.find_related_procedures(procedure, max_depth=2)
                for rel_proc in related[:2]:  # Top 2 related
                    rel_context = self.graph.get_procedure_context(rel_proc['procedure'])
                    if rel_context:
                        # Score based on distance in graph
                        distance_score = 1.0 / (1 + rel_proc['distance'])
                        
                        graph_results.append({
                            'text': self._format_graph_context(rel_context),
                            'metadata': {
                                'source': 'knowledge_graph',
                                'procedure': rel_proc['procedure'],
                                'related_to': procedure,
                                'distance': rel_proc['distance'],
                                'entities': rel_context
                            },
                            'retrieval_source': 'graph',
                            'graph_score': distance_score
                        })
            
            except Exception as e:
                logger.warning(f"Graph retrieval failed for '{procedure}': {e}")
        
        # Sort by graph score and limit
        graph_results.sort(key=lambda x: x['graph_score'], reverse=True)
        return graph_results[:top_k]
    
    def _format_graph_context(self, context: Dict[str, Any]) -> str:
        """
        Format graph context into readable text.
        
        Args:
            context: Graph context dictionary
        
        Returns:
            Formatted text string
        """
        parts = [f"Procedure: {context['procedure']}"]
        
        if context.get('description'):
            parts.append(f"Description: {context['description']}")
        
        if context.get('anatomy'):
            parts.append(f"Anatomical Structures: {', '.join(context['anatomy'])}")
        
        if context.get('instruments'):
            parts.append(f"Required Instruments: {', '.join(context['instruments'])}")
        
        if context.get('techniques'):
            parts.append(f"Techniques: {', '.join(context['techniques'])}")
        
        if context.get('complications'):
            parts.append(f"Potential Complications: {', '.join(context['complications'])}")
        
        if context.get('medications'):
            parts.append(f"Medications: {', '.join(context['medications'])}")
        
        return "\n".join(parts)
    
    def _merge_results(self, 
                      vector_results: List[Dict[str, Any]], 
                      graph_results: List[Dict[str, Any]], 
                      top_k: int) -> List[Dict[str, Any]]:
        """
        Merge and re-rank vector and graph results.
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            top_k: Number of final results
        
        Returns:
            Merged and ranked results
        """
        # Normalize scores
        all_results = []
        
        # Add vector results with weighted scores
        for result in vector_results:
            result['final_score'] = result.get('vector_score', 0.0) * self.vector_weight
            all_results.append(result)
        
        # Add graph results with weighted scores
        for result in graph_results:
            result['final_score'] = result.get('graph_score', 0.0) * self.graph_weight
            all_results.append(result)
        
        # Remove duplicates based on text similarity
        unique_results = self._deduplicate_results(all_results)
        
        # Sort by final score
        unique_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return unique_results[:top_k]
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate results based on text similarity.
        
        Args:
            results: List of results to deduplicate
        
        Returns:
            Deduplicated results
        """
        unique = []
        seen_texts = set()
        
        for result in results:
            text = result.get('text', '')
            # Simple deduplication - in production, use better similarity measure
            text_key = text[:100].lower().strip()  # First 100 chars as key
            
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique.append(result)
        
        return unique
    
    def _expand_with_graph_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Expand results with additional graph context.
        
        Args:
            results: Retrieved results
        
        Returns:
            Results enriched with graph context
        """
        for result in results:
            # Extract entities from result text
            text = result.get('text', '')
            entities = self.extractor.extract_entities(text)
            
            # Add entity information to metadata
            if 'metadata' not in result:
                result['metadata'] = {}
            
            result['metadata']['extracted_entities'] = entities
            
            # For procedures, add related procedures
            procedures = entities.get('procedures', [])
            if procedures:
                main_procedure = procedures[0]
                try:
                    related = self.graph.find_related_procedures(main_procedure, max_depth=1)
                    if related:
                        result['metadata']['related_procedures'] = [
                            r['procedure'] for r in related[:3]
                        ]
                except Exception as e:
                    logger.debug(f"Could not find related procedures: {e}")
        
        return results
    
    def retrieve_by_entity(self, 
                          entity_type: str, 
                          entity_name: str, 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve information specifically about an entity.
        
        Args:
            entity_type: Type of entity (Procedure, Anatomy, etc.)
            entity_name: Name of the entity
            top_k: Number of results
        
        Returns:
            Retrieved results about the entity
        """
        # Get graph context for the entity
        if entity_type == 'Procedure':
            context = self.graph.get_procedure_context(entity_name)
            if context:
                return [{
                    'text': self._format_graph_context(context),
                    'metadata': {
                        'source': 'knowledge_graph',
                        'entity_type': entity_type,
                        'entity_name': entity_name,
                        'context': context
                    },
                    'score': 1.0
                }]
        
        # Fall back to vector search
        query = f"{entity_type}: {entity_name}"
        return self._vector_retrieve(query, top_k)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Graph statistics
        """
        return self.graph.get_graph_statistics()
