"""
Retrieval Confidence Scoring
Computes composite confidence scores for retrieval quality and answer reliability.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Computes multi-dimensional confidence scores for retrieved results and generated answers.
    
    Confidence components:
    1. Retrieval similarity: Average cosine similarity of retrieved chunks
    2. Graph coverage: Proportion of query entities found in knowledge graph
    3. Source agreement: Consistency across multiple retrieved chunks  
    4. Verification rate: Percentage of claims verified by graph (if available)
    """
    
    def __init__(self, 
                 retrieval_weight: float = 0.30,
                 graph_coverage_weight: float = 0.25,
                 source_agreement_weight: float = 0.20,
                 verification_weight: float = 0.25):
        """
        Initialize confidence scorer with component weights.
        
        Args:
            retrieval_weight: Weight for retrieval similarity score (0-1)
            graph_coverage_weight: Weight for graph coverage score (0-1)
            source_agreement_weight: Weight for source agreement score (0-1)
            verification_weight: Weight for verification score (0-1)
        """
        # Normalize weights to sum to 1
        total = retrieval_weight + graph_coverage_weight + source_agreement_weight + verification_weight
        self.retrieval_weight = retrieval_weight / total
        self.graph_coverage_weight = graph_coverage_weight / total
        self.source_agreement_weight = source_agreement_weight / total
        self.verification_weight = verification_weight / total
        
        logger.info(f"Confidence scorer initialized with weights: retrieval={self.retrieval_weight:.2f}, "
                   f"graph_coverage={self.graph_coverage_weight:.2f}, "
                   f"source_agreement={self.source_agreement_weight:.2f}, "
                   f"verification={self.verification_weight:.2f}")
    
    def compute_confidence(self,
                          contexts: List[Dict[str, Any]],
                          query_entities: Optional[List[str]] = None,
                          graph_entities: Optional[List[str]] = None,
                          verification_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Compute composite confidence score.
        
        Args:
            contexts: Retrieved context chunks with scores
            query_entities: Entities extracted from query (optional)
            graph_entities: Entities found in graph (optional)
            verification_score: Graph verification score 0-1 (optional)
        
        Returns:
            Dictionary with confidence metrics:
            {
                'overall_confidence': float (0-1),'confidence_level': str ('high'/'medium'/'low'),
                'retrieval_similarity': float,
                'graph_coverage': float,
                'source_agreement': float,
                'verification_score': float,
                'components': dict,
                'warning_message': str (optional)
            }
        """
        # Component 1: Retrieval similarity
        retrieval_sim = self._compute_retrieval_similarity(contexts)
        
        # Component 2: Graph coverage
        graph_coverage = self._compute_graph_coverage(query_entities, graph_entities)
        
        # Component 3: Source agreement
        source_agreement = self._compute_source_agreement(contexts)
        
        # Component 4: Verification score (if available)
        verification = verification_score if verification_score is not None else 1.0
        
        # Compute weighted confidence
        overall_confidence = (
            self.retrieval_weight * retrieval_sim +
            self.graph_coverage_weight * graph_coverage +
            self.source_agreement_weight * source_agreement +
            self.verification_weight * verification
        )
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(overall_confidence)
        
        # Generate warning if needed
        warning_message = self._generate_warning(confidence_level, overall_confidence)
        
        result = {
            'overall_confidence': round(overall_confidence, 3),
            'confidence_level': confidence_level,
            'retrieval_similarity': round(retrieval_sim, 3),
            'graph_coverage': round(graph_coverage, 3),
            'source_agreement': round(source_agreement, 3),
            'verification_score': round(verification, 3),
            'components': {
                'retrieval': {'score': round(retrieval_sim, 3), 'weight': self.retrieval_weight},
                'graph_coverage': {'score': round(graph_coverage, 3), 'weight': self.graph_coverage_weight},
                'source_agreement': {'score': round(source_agreement, 3), 'weight': self.source_agreement_weight},
                'verification': {'score': round(verification, 3), 'weight': self.verification_weight}
            }
        }
        
        if warning_message:
            result['warning_message'] = warning_message
        
        return result
    
    def _compute_retrieval_similarity(self, contexts: List[Dict[str, Any]]) -> float:
        """
        Compute average retrieval similarity score.
        
        Args:
            contexts: Retrieved contexts with 'score' field
        
        Returns:
            Average similarity score (0-1)
        """
        if not contexts:
            return 0.0
        
        scores = [c.get('score', 0.0) for c in contexts]
        
        # Filter out invalid scores
        valid_scores = [s for s in scores if s > -1e30]
        
        if not valid_scores:
            return 0.0
        
        # Average of top scores
        avg_score = np.mean(valid_scores)
        
        # Normalize to 0-1 if needed (cosine similarity is already 0-1)
        # FAISS scores can be negative for some metrics, so clip
        normalized = np.clip(avg_score, 0.0, 1.0)
        
        return float(normalized)
    
    def _compute_graph_coverage(self, 
                                query_entities: Optional[List[str]], 
                                graph_entities: Optional[List[str]]) -> float:
        """
        Compute graph coverage: proportion of query entities found in graph.
        
        Args:
            query_entities: Entities extracted from query
            graph_entities: Entities found in knowledge graph
        
        Returns:
            Coverage score (0-1)
        """
        if not query_entities:
            return 1.0  # No entities to find, perfect coverage
        
        if not graph_entities:
            return 0.0  # No graph entities found
        
        # Case-insensitive matching
        query_set = {e.lower() for e in query_entities}
        graph_set = {e.lower() for e in graph_entities}
        
        # Calculate overlap
        found = query_set.intersection(graph_set)
        coverage = len(found) / len(query_set)
        
        return float(coverage)
    
    def _compute_source_agreement(self, contexts: List[Dict[str, Any]]) -> float:
        """
        Compute source agreement: consistency across retrieved chunks.
        
        Uses heuristics:
        - Higher scores for multiple diverse sources
        - Lower scores for single source or very different similarity scores
        
        Args:
            contexts: Retrieved contexts
        
        Returns:
            Agreement score (0-1)
        """
        if not contexts:
            return 0.0
        
        if len(contexts) == 1:
            return 0.5  # Single source: medium confidence
        
        # Check source diversity
        sources = set()
        for c in contexts:
            source = c.get('metadata', {}).get('source', '')
            if source:
                sources.add(source)
        
        # More unique sources = higher agreement
        source_diversity = len(sources) / len(contexts)
        
        # Check score consistency (lower variance = higher agreement)
        scores = [c.get('score', 0.0) for c in contexts if c.get('score', 0.0) > -1e30]
        
        if len(scores) >= 2:
            score_variance = np.var(scores)
            # Normalize variance: high variance = low consistency
            # Assume variance in range [0, 0.1]
            consistency = 1.0 - min(score_variance * 10, 1.0)
        else:
            consistency = 0.5
        
        # Combine diversity and consistency
        agreement = 0.6 * source_diversity + 0.4 * consistency
        
        return float(np.clip(agreement, 0.0, 1.0))
    
    def _get_confidence_level(self, overall_confidence: float) -> str:
        """
        Map confidence score to level.
        
        Args:
            overall_confidence: Overall confidence score (0-1)
        
        Returns:
            'high', 'medium', or 'low'
        """
        if overall_confidence >= 0.80:
            return 'high'
        elif overall_confidence >= 0.50:
            return 'medium'
        else:
            return 'low'
    
    def _generate_warning(self, confidence_level: str, score: float) -> Optional[str]:
        """
        Generate appropriate warning message based on confidence.
        
        Args:
            confidence_level: 'high', 'medium', or 'low'
            score: Confidence score
        
        Returns:
            Warning message or None
        """
        if confidence_level == 'high':
            return None
        elif confidence_level == 'medium':
            return f"⚠️ Medium confidence ({score:.0%}). Based on available guidelines; verify with attending or senior resident before clinical application."
        else:
            return f"🔴 Low confidence ({score:.0%}). Insufficient evidence in knowledge base. Consult supervisor or primary sources before use."
    
    def format_confidence_for_user(self, confidence_report: Dict[str, Any]) -> str:
        """
        Format confidence report for end-user display.
        
        Args:
            confidence_report: Confidence report from compute_confidence()
        
        Returns:
            Formatted string
        """
        score = confidence_report['overall_confidence']
        level = confidence_report['confidence_level']
        
        # Confidence indicator
        if level == 'high':
            indicator = "✅ HIGH CONFIDENCE"
        elif level == 'medium':
            indicator = "⚠️ MEDIUM CONFIDENCE"
        else:
            indicator = "🔴 LOW CONFIDENCE"
        
        message = f"\n\n{indicator} ({score:.0%})\n"
        
        # Component breakdown
        message += "Confidence Components:\n"
        message += f"  • Retrieval Quality: {confidence_report['retrieval_similarity']:.0%}\n"
        message += f"  • Graph Coverage: {confidence_report['graph_coverage']:.0%}\n"
        message += f"  • Source Agreement: {confidence_report['source_agreement']:.0%}\n"
        message += f"  • Verification: {confidence_report['verification_score']:.0%}\n"
        
        # Add warning if present
        if 'warning_message' in confidence_report:
            message += f"\n{confidence_report['warning_message']}\n"
        
        return message
