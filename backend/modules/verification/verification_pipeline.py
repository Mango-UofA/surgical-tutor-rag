"""
Complete Verification Pipeline
Integrates claim extraction, graph verification, hallucination taxonomy, and abstention.
"""

from typing import Dict, Any, Optional
import logging
from .claim_extractor import ClaimExtractor
from .graph_verifier import GraphVerifier
from .surgical_hallucination_taxonomy import SurgicalHallucinationTaxonomy
from .abstention_policy import AbstentionPolicy, UncertaintyQuantifier
from ..graph.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)


class VerificationPipeline:
    """
    Complete pipeline for answer verification:
    1. Extract claims from answer
    2. Verify claims against knowledge graph
    3. Classify hallucinations using taxonomy
    4. Compute verification metrics
    5. Apply abstention policy
    6. Generate verification report
    """
    
    def __init__(self, 
                 neo4j_manager: Neo4jManager,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 abstention_threshold: float = 0.5,
                 enable_abstention: bool = True):
        """
        Initialize verification pipeline with all enhancement modules.
        
        Args:
            neo4j_manager: Neo4j graph database manager
            api_key: OpenAI API key
            base_url: OpenAI base URL
            model: Model name (e.g., 'gpt-4o')
            abstention_threshold: Minimum verification score to answer
            enable_abstention: Whether to enable abstention mechanism
        """
        self.claim_extractor = ClaimExtractor(api_key, base_url, model)
        self.graph_verifier = GraphVerifier(neo4j_manager)
        self.taxonomy = SurgicalHallucinationTaxonomy()
        self.abstention_policy = AbstentionPolicy(abstention_threshold, enable_abstention)
        self.uncertainty_quantifier = UncertaintyQuantifier()
    
    def verify_answer(self, query: str, answer: str) -> Dict[str, Any]:
        """
        Complete verification of a generated answer with taxonomy and abstention.
        
        Args:
            query: Original user query
            answer: Generated answer to verify
        
        Returns:
            Complete verification report:
            {
                'verification_score': float,
                'confidence_level': str,
                'total_claims': int,
                'verified_claims': int,
                'unverified_claims': int,
                'category_scores': {...},
                'unverified_details': [...],
                'extracted_claims': {...},
                'hallucination_analysis': {...},  # NEW: Taxonomy classification
                'abstention_decision': {...},    # NEW: Abstention analysis
                'uncertainty_analysis': {...},   # NEW: Uncertainty quantification
                'warning_message': str (optional)
            }
        """
        logger.info(f"Starting verification for query: {query[:100]}...")
        
        # Step 1: Extract claims
        logger.info("Extracting claims from answer...")
        extracted_claims = self.claim_extractor.extract_claims(answer, query)
        total_extracted = self.claim_extractor.count_total_claims(extracted_claims)
        logger.info(f"Extracted {total_extracted} claims")
        
        # Step 2: Verify claims
        logger.info("Verifying claims against knowledge graph...")
        verification_results = self.graph_verifier.verify_claims(extracted_claims)
        
        # Step 3: Apply hallucination taxonomy (NEW)
        logger.info("Classifying hallucinations...")
        hallucination_analysis = self.taxonomy.generate_error_report(verification_results)
        
        # Step 4: Determine confidence level
        confidence_level = self.graph_verifier.get_verification_confidence_level(
            verification_results['verification_score']
        )
        
        # Step 5: Check abstention policy (NEW)
        logger.info("Evaluating abstention policy...")
        verification_results['confidence_level'] = confidence_level
        should_abstain, abstention_reason = self.abstention_policy.should_abstain(verification_results)
        
        # Step 6: Quantify uncertainty (NEW)
        uncertainty_analysis = self.uncertainty_quantifier.calculate_overall_uncertainty(
            verification_results
        )
        
        # Step 7: Generate warning message
        warning_message = self._generate_warning_message(
            confidence_level,
            verification_results['verification_score'],
            hallucination_analysis
        )
        
        # Compile complete report
        report = {
            'verification_score': verification_results['verification_score'],
            'confidence_level': confidence_level,
            'total_claims': verification_results['total_claims'],
            'verified_claims': verification_results['verified_claims'],
            'unverified_claims': verification_results['unverified_claims'],
            'category_scores': verification_results['category_scores'],
            'unverified_details': verification_results['unverified_details'],
            'extracted_claims': extracted_claims,
            'hallucination_analysis': hallucination_analysis,  # NEW
            'abstention_decision': {                           # NEW
                'should_abstain': should_abstain,
                'reason': abstention_reason
            },
            'uncertainty_analysis': uncertainty_analysis,      # NEW
        }
        
        if warning_message:
            report['warning_message'] = warning_message
        
        logger.info(f"Verification complete: {verification_results['verified_claims']}/{verification_results['total_claims']} claims verified (score: {verification_results['verification_score']:.2f})")
        logger.info(f"Hallucinations detected: {hallucination_analysis['total_hallucinations']}")
        logger.info(f"Abstention decision: {'ABSTAIN' if should_abstain else 'PROCEED'}")
        
        return report
    
    def _generate_warning_message(self, confidence_level: str, score: float, hallucination_analysis: Optional[Dict] = None) -> Optional[str]:
        """Generate appropriate warning message based on confidence level and hallucination analysis."""
        warnings = []
        
        # Base confidence warning
        if confidence_level == 'medium':
            warnings.append("⚠️ Based on available guidelines; verify with attending or senior resident before clinical application.")
        elif confidence_level == 'low' or confidence_level == 'critical':
            warnings.append("⚠️ CAUTION: Insufficient evidence in knowledge base. Consult supervisor or primary sources before use.")
        
        # Hallucination-specific warnings
        if hallucination_analysis:
            critical_errors = sum(1 for h in hallucination_analysis.get('hallucinations', []) 
                                if h.get('severity') == 'critical')
            high_errors = sum(1 for h in hallucination_analysis.get('hallucinations', []) 
                            if h.get('severity') == 'high')
            
            if critical_errors > 0:
                warnings.append(f"🔴 CRITICAL: {critical_errors} critical hallucination(s) detected. DO NOT USE for patient care.")
            elif high_errors > 0:
                warnings.append(f"⚠️ WARNING: {high_errors} high-severity hallucination(s) detected. Verify before use.")
        
        return "\n".join(warnings) if warnings else None
    
    def format_verification_for_user(self, verification_report: Dict[str, Any]) -> str:
        """
        Format verification results for end-user display.
        
        Args:
            verification_report: Verification report from verify_answer()
        
        Returns:
            Formatted string for display
        """
        score = verification_report['verification_score']
        confidence = verification_report['confidence_level']
        verified = verification_report['verified_claims']
        total = verification_report['total_claims']
        
        # Check abstention decision
        if verification_report.get('abstention_decision', {}).get('should_abstain', False):
            return self._format_abstention_message(verification_report)
        
        # Confidence indicator
        if confidence == 'high':
            indicator = "✅ HIGH CONFIDENCE"
        elif confidence == 'medium':
            indicator = "⚠️ MEDIUM CONFIDENCE"
        else:
            indicator = "🔴 LOW CONFIDENCE"
        
        message = f"\n\n{indicator}\n"
        message += f"Verification: {verified}/{total} claims verified against knowledge graph ({score:.0%})\n"
        
        # Add warning if present
        if 'warning_message' in verification_report:
            message += f"\n{verification_report['warning_message']}\n"
        
        # Add hallucination analysis
        if 'hallucination_analysis' in verification_report:
            hall_analysis = verification_report['hallucination_analysis']
            if hall_analysis.get('total_hallucinations', 0) > 0:
                message += f"\n🔍 Hallucination Detection:\n"
                message += f"  • Total: {hall_analysis['total_hallucinations']}\n"
                message += f"  • Safety Score: {hall_analysis.get('safety_score', 0):.2f}/1.00\n"
                
                # Show breakdown by severity
                severity_counts = hall_analysis.get('severity_distribution', {})
                if severity_counts:
                    message += f"  • Severity: "
                    parts = []
                    if severity_counts.get('critical', 0) > 0:
                        parts.append(f"Critical: {severity_counts['critical']}")
                    if severity_counts.get('high', 0) > 0:
                        parts.append(f"High: {severity_counts['high']}")
                    if severity_counts.get('medium', 0) > 0:
                        parts.append(f"Medium: {severity_counts['medium']}")
                    if severity_counts.get('low', 0) > 0:
                        parts.append(f"Low: {severity_counts['low']}")
                    message += ", ".join(parts) + "\n"
        
        # Add uncertainty analysis
        if 'uncertainty_analysis' in verification_report:
            uncertainty = verification_report['uncertainty_analysis']
            overall = uncertainty.get('overall_uncertainty', 0)
            message += f"\n📊 Uncertainty: {(1-overall)*100:.0f}% certain\n"
        
        # Add category breakdown
        cat_scores = verification_report['category_scores']
        if any(v > 0 for v in cat_scores.values()):
            message += f"\nCategory Verification:\n"
            if cat_scores.get('instruments', 0) > 0:
                message += f"  • Instruments: {cat_scores['instruments']:.0%}\n"
            if cat_scores.get('step_order', 0) > 0:
                message += f"  • Step Order: {cat_scores['step_order']:.0%}\n"
            if cat_scores.get('anatomy', 0) > 0:
                message += f"  • Anatomy: {cat_scores['anatomy']:.0%}\n"
            if cat_scores.get('complications', 0) > 0:
                message += f"  • Complications: {cat_scores['complications']:.0%}\n"
        
        return message
    
    def _format_abstention_message(self, verification_report: Dict[str, Any]) -> str:
        """Format abstention response when system refuses to answer."""
        abstention = verification_report.get('abstention_decision', {})
        reason = abstention.get('reason', 'Unknown reason')
        
        message = "\n\n🛑 SYSTEM ABSTENTION\n"
        message += "The system has determined it cannot provide a safe answer for this query.\n\n"
        message += f"Reason: {reason}\n\n"
        message += "Recommendation: Please consult:\n"
        message += "  • Attending surgeon or senior resident\n"
        message += "  • Primary surgical literature\n"
        message += "  • Institutional protocols\n\n"
        message += "Patient safety is our priority. When in doubt, we abstain.\n"
        
        return message
