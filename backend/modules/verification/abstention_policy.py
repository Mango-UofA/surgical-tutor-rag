"""
Uncertainty-Triggered Abstention Module
System refuses to answer when verification confidence is below safety threshold.

Novel contribution for MICCAI: First automated abstention mechanism for 
surgical RAG systems based on knowledge graph verification confidence.
"""

from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AbstentionPolicy:
    """
    Defines when the RAG system should refuse to answer due to insufficient confidence.
    
    Safety-first approach: Better to say "I don't know" than provide unverified 
    information in clinical/educational contexts.
    """
    
    # Confidence thresholds for abstention
    CRITICAL_THRESHOLD = 0.5   # Below 50% verified → abstain
    WARNING_THRESHOLD = 0.7    # 50-70% verified → warn user
    SAFE_THRESHOLD = 0.8       # Above 80% verified → safe to present
    
    def __init__(self, 
                 abstention_threshold: float = 0.5,
                 enable_abstention: bool = True):
        """
        Initialize abstention policy.
        
        Args:
            abstention_threshold: Minimum verification score to answer (0-1)
            enable_abstention: Whether to enable abstention (disable for testing)
        """
        self.abstention_threshold = abstention_threshold
        self.enable_abstention = enable_abstention
        
        logger.info(f"Abstention policy initialized (threshold: {abstention_threshold:.2f}, enabled: {enable_abstention})")
    
    def should_abstain(self, verification_results: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if system should refuse to answer.
        
        Args:
            verification_results: Results from VerificationPipeline
        
        Returns:
            Tuple of (should_abstain: bool, reason: str)
        """
        if not self.enable_abstention:
            return False, ""
        
        verification_score = verification_results.get('verification_score', 0.0)
        confidence_level = verification_results.get('confidence_level', 'low')
        total_claims = verification_results.get('total_claims', 0)
        
        # Case 1: No claims extracted → likely too vague to verify
        if total_claims == 0:
            return True, "Unable to extract verifiable claims from answer. Question may be too vague or outside knowledge base."
        
        # Case 2: Verification score below threshold
        if verification_score < self.abstention_threshold:
            return True, f"Insufficient verification confidence ({verification_score:.0%}). Only {verification_results.get('verified_claims', 0)}/{total_claims} claims verified in knowledge graph."
        
        # Case 3: Critical hallucinations detected
        unverified_details = verification_results.get('unverified_details', [])
        critical_errors = self._count_critical_errors(unverified_details)
        
        if critical_errors > 0:
            return True, f"Detected {critical_errors} critical error(s) in answer. Cannot provide safe response."
        
        # All checks passed
        return False, ""
    
    def _count_critical_errors(self, unverified_details: list) -> int:
        """Count critical errors that warrant abstention."""
        critical_keywords = ['dosage', 'contraindication', 'complication management', 'anatomy']
        critical_count = 0
        
        for detail in unverified_details:
            claim = str(detail.get('claim', '')).lower()
            if any(keyword in claim for keyword in critical_keywords):
                critical_count += 1
        
        return critical_count
    
    def get_confidence_level(self, verification_score: float) -> str:
        """Map verification score to confidence level."""
        if verification_score >= self.SAFE_THRESHOLD:
            return 'high'
        elif verification_score >= self.WARNING_THRESHOLD:
            return 'medium'
        elif verification_score >= self.CRITICAL_THRESHOLD:
            return 'low'
        else:
            return 'critical'
    
    def format_abstention_response(self, 
                                   query: str,
                                   reason: str,
                                   verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a user-friendly abstention message.
        
        Args:
            query: Original user query
            reason: Reason for abstention
            verification_results: Full verification results
        
        Returns:
            Formatted abstention response
        """
        verification_score = verification_results.get('verification_score', 0.0)
        verified_claims = verification_results.get('verified_claims', 0)
        total_claims = verification_results.get('total_claims', 0)
        
        message = f"""🔴 **Unable to Provide Safe Answer**

I cannot answer this question with sufficient confidence to ensure patient safety.

**Reason:** {reason}

**What I found:**
• Verification confidence: {verification_score:.0%}
• Verified claims: {verified_claims}/{total_claims}

**Why this matters:**
In surgical education and clinical contexts, providing unverified information could lead to patient harm. I prioritize safety over completeness.

**What you can do:**
1. **Consult primary sources:** Review surgical guidelines directly
2. **Ask a more specific question:** Include procedure name, step, or context
3. **Upload more documents:** Expand the knowledge base
4. **Consult an expert:** Speak with attending surgeon or senior resident

**Query:** {query}
"""
        
        return {
            'abstained': True,
            'answer': message,
            'verification_score': verification_score,
            'verified_claims': verified_claims,
            'total_claims': total_claims,
            'reason': reason,
            'confidence_level': 'abstained'
        }
    
    def format_warning_response(self,
                               answer: str,
                               verification_results: Dict[str, Any]) -> str:
        """
        Add warning banner to low-confidence answers.
        
        Args:
            answer: Generated answer
            verification_results: Verification results
        
        Returns:
            Answer with warning banner
        """
        verification_score = verification_results.get('verification_score', 0.0)
        confidence_level = self.get_confidence_level(verification_score)
        
        if confidence_level == 'high':
            return answer  # No warning needed
        
        elif confidence_level == 'medium':
            warning = f"""⚠️ **MEDIUM CONFIDENCE ({verification_score:.0%} verified)**
This answer is based on available guidelines but has not been fully verified. Please cross-reference with primary sources before clinical application.

---

"""
            return warning + answer
        
        elif confidence_level == 'low':
            warning = f"""⚠️ **LOW CONFIDENCE ({verification_score:.0%} verified)**
This answer has limited verification in the knowledge base. Use with caution and consult supervisor or primary literature.

---

"""
            return warning + answer
        
        else:  # critical
            # Should have been abstained, but add emergency warning
            warning = f"""🔴 **CRITICAL: UNVERIFIED INFORMATION ({verification_score:.0%})**
This answer could not be adequately verified. DO NOT use for clinical decisions without expert consultation.

---

"""
            return warning + answer


class UncertaintyQuantifier:
    """
    Quantifies uncertainty in RAG system responses.
    
    Tracks multiple sources of uncertainty:
    1. Verification confidence (graph-based)
    2. Retrieval confidence (vector similarity)
    3. Generation confidence (model uncertainty)
    """
    
    def __init__(self):
        self.uncertainty_log = []
    
    def calculate_overall_uncertainty(self,
                                     verification_results: Dict[str, Any],
                                     retrieval_scores: list = None,
                                     generation_metadata: Dict = None) -> Dict[str, Any]:
        """
        Calculate overall system uncertainty from multiple sources.
        
        Args:
            verification_results: Graph verification results
            retrieval_scores: Vector similarity scores from retrieval
            generation_metadata: LLM generation metadata (temperature, etc.)
        
        Returns:
            Comprehensive uncertainty analysis
        """
        verification_certainty = verification_results.get('verification_score', 0.0)
        
        # Retrieval certainty (based on similarity scores)
        if retrieval_scores:
            avg_retrieval_score = sum(retrieval_scores) / len(retrieval_scores)
            retrieval_certainty = min(1.0, avg_retrieval_score)  # Normalize to 0-1
        else:
            retrieval_certainty = 0.5  # Unknown
        
        # Generation certainty (inverse of temperature, or fixed if not available)
        if generation_metadata and 'temperature' in generation_metadata:
            temperature = generation_metadata['temperature']
            generation_certainty = 1.0 - min(1.0, temperature)  # Lower temp = higher certainty
        else:
            generation_certainty = 0.5  # Assume moderate
        
        # Weighted combination (verification is most important)
        overall_certainty = (
            verification_certainty * 0.6 +   # 60% weight on graph verification
            retrieval_certainty * 0.3 +      # 30% weight on retrieval quality
            generation_certainty * 0.1       # 10% weight on generation
        )
        
        uncertainty = 1.0 - overall_certainty
        
        result = {
            'overall_certainty': overall_certainty,
            'overall_uncertainty': uncertainty,
            'components': {
                'verification_certainty': verification_certainty,
                'retrieval_certainty': retrieval_certainty,
                'generation_certainty': generation_certainty
            },
            'interpretation': self._interpret_uncertainty(uncertainty)
        }
        
        # Log for analysis
        self.uncertainty_log.append(result)
        
        return result
    
    def _interpret_uncertainty(self, uncertainty: float) -> str:
        """Provide human-readable interpretation of uncertainty."""
        if uncertainty < 0.2:
            return "Very High Confidence"
        elif uncertainty < 0.4:
            return "High Confidence"
        elif uncertainty < 0.6:
            return "Moderate Confidence"
        elif uncertainty < 0.8:
            return "Low Confidence"
        else:
            return "Very Low Confidence - Abstain"
    
    def get_uncertainty_statistics(self) -> Dict[str, Any]:
        """Get statistics from logged uncertainty measurements."""
        if not self.uncertainty_log:
            return {'message': 'No uncertainty data logged'}
        
        uncertainties = [u['overall_uncertainty'] for u in self.uncertainty_log]
        
        return {
            'total_queries': len(uncertainties),
            'mean_uncertainty': sum(uncertainties) / len(uncertainties),
            'max_uncertainty': max(uncertainties),
            'min_uncertainty': min(uncertainties),
            'abstention_rate': sum(1 for u in uncertainties if u > 0.5) / len(uncertainties)
        }


# For backward compatibility and easy imports
def should_abstain_from_answer(verification_results: Dict[str, Any],
                               threshold: float = 0.5) -> Tuple[bool, str]:
    """
    Convenience function to check if system should abstain.
    
    Args:
        verification_results: Verification results from pipeline
        threshold: Abstention threshold (default: 0.5)
    
    Returns:
        (should_abstain, reason)
    """
    policy = AbstentionPolicy(abstention_threshold=threshold)
    return policy.should_abstain(verification_results)
