"""
Surgical Hallucination Taxonomy
Categorizes error types in surgical RAG answers for safety analysis.

Novel contribution for MICCAI: First domain-specific hallucination taxonomy 
for surgical education, enabling granular error analysis and targeted improvements.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HallucinationType(Enum):
    """Categories of surgical hallucinations."""
    
    # Anatomical Errors
    ANATOMICAL_STRUCTURE_ERROR = "anatomical_structure_error"  # Wrong organ/structure
    ANATOMICAL_LOCATION_ERROR = "anatomical_location_error"    # Wrong location
    ANATOMICAL_RELATIONSHIP_ERROR = "anatomical_relationship_error"  # Wrong spatial relationship
    
    # Instrument Errors
    INSTRUMENT_INCORRECT = "instrument_incorrect"  # Wrong instrument for step
    INSTRUMENT_NONEXISTENT = "instrument_nonexistent"  # Invented instrument
    INSTRUMENT_USAGE_ERROR = "instrument_usage_error"  # Wrong technique/usage
    
    # Procedural Errors
    STEP_ORDER_ERROR = "step_order_error"  # Wrong sequence
    STEP_OMISSION = "step_omission"  # Missing critical step
    STEP_FABRICATION = "step_fabrication"  # Invented step
    TECHNIQUE_ERROR = "technique_error"  # Wrong surgical technique
    
    # Complication Errors
    COMPLICATION_EXAGGERATED = "complication_exaggerated"  # Overstated risk
    COMPLICATION_MINIMIZED = "complication_minimized"  # Understated risk
    COMPLICATION_INVENTED = "complication_invented"  # Nonexistent complication
    MANAGEMENT_ERROR = "management_error"  # Wrong complication management
    
    # Contraindication Errors
    CONTRAINDICATION_MISSED = "contraindication_missed"  # Missing warning
    CONTRAINDICATION_INVENTED = "contraindication_invented"  # False warning
    
    # Quantitative Errors
    DOSAGE_ERROR = "dosage_error"  # Wrong medication dose
    MEASUREMENT_ERROR = "measurement_error"  # Wrong measurement/size
    STATISTIC_ERROR = "statistic_error"  # Wrong outcome data
    
    # Source Attribution Errors
    NO_CITATION = "no_citation"  # Claim without source
    FALSE_CITATION = "false_citation"  # Citation doesn't support claim
    OUTDATED_INFORMATION = "outdated_information"  # Superseded guidelines


class SurgicalHallucinationTaxonomy:
    """
    Classifies and tracks hallucination patterns in surgical RAG outputs.
    
    Use cases:
    1. Error analysis for targeted improvements
    2. Safety monitoring in production
    3. MICCAI paper contribution: First surgical hallucination taxonomy
    """
    
    def __init__(self):
        self.taxonomy = self._build_taxonomy()
    
    def _build_taxonomy(self) -> Dict[str, Dict[str, Any]]:
        """Build complete taxonomy with detection rules."""
        return {
            # Anatomical Category
            HallucinationType.ANATOMICAL_STRUCTURE_ERROR.value: {
                'category': 'anatomical',
                'severity': 'critical',
                'description': 'Incorrect anatomical structure mentioned',
                'example': 'Appendix located in upper left quadrant',
                'detection_rules': ['anatomy_claims_unverified']
            },
            HallucinationType.ANATOMICAL_LOCATION_ERROR.value: {
                'category': 'anatomical',
                'severity': 'critical',
                'description': 'Wrong anatomical location specified',
                'example': 'Laparoscopic port placed through liver',
                'detection_rules': ['spatial_relationship_error']
            },
            
            # Instrument Category
            HallucinationType.INSTRUMENT_INCORRECT.value: {
                'category': 'instrument',
                'severity': 'high',
                'description': 'Wrong instrument specified for surgical step',
                'example': 'Use scalpel for laparoscopic dissection',
                'detection_rules': ['instrument_claims_unverified']
            },
            HallucinationType.INSTRUMENT_NONEXISTENT.value: {
                'category': 'instrument',
                'severity': 'critical',
                'description': 'Fabricated or nonexistent surgical instrument',
                'example': 'Quantum endoscopic dissector',
                'detection_rules': ['instrument_not_in_graph']
            },
            
            # Procedural Category
            HallucinationType.STEP_ORDER_ERROR.value: {
                'category': 'procedural',
                'severity': 'critical',
                'description': 'Incorrect ordering of surgical steps',
                'example': 'Close incision before removing specimen',
                'detection_rules': ['step_order_claims_unverified']
            },
            HallucinationType.STEP_FABRICATION.value: {
                'category': 'procedural',
                'severity': 'high',
                'description': 'Invented surgical step not in procedure',
                'example': 'Perform triple somersault maneuver',
                'detection_rules': ['step_not_in_procedure']
            },
            
            # Complication Category
            HallucinationType.COMPLICATION_EXAGGERATED.value: {
                'category': 'complication',
                'severity': 'medium',
                'description': 'Overstated complication risk/severity',
                'example': '50% mortality rate for appendectomy',
                'detection_rules': ['statistic_exceeds_literature']
            },
            HallucinationType.MANAGEMENT_ERROR.value: {
                'category': 'complication',
                'severity': 'critical',
                'description': 'Incorrect complication management advice',
                'example': 'Ignore bleeding and continue',
                'detection_rules': ['management_contradicts_guidelines']
            },
            
            # Quantitative Category
            HallucinationType.DOSAGE_ERROR.value: {
                'category': 'quantitative',
                'severity': 'critical',
                'description': 'Incorrect medication dosage',
                'example': '10g aspirin daily',
                'detection_rules': ['dosage_out_of_range']
            },
            HallucinationType.STATISTIC_ERROR.value: {
                'category': 'quantitative',
                'severity': 'medium',
                'description': 'Fabricated or incorrect statistics',
                'example': '99.9% success rate (literature shows 85%)',
                'detection_rules': ['number_not_in_context']
            },
            
            # Source Attribution Category
            HallucinationType.NO_CITATION.value: {
                'category': 'attribution',
                'severity': 'low',
                'description': 'Factual claim without citation',
                'example': 'Studies show...',
                'detection_rules': ['citation_coverage_low']
            },
            HallucinationType.FALSE_CITATION.value: {
                'category': 'attribution',
                'severity': 'high',
                'description': 'Citation does not support claim',
                'example': 'According to Smith 2020 [unrelated paper]',
                'detection_rules': ['citation_content_mismatch']
            }
        }
    
    def classify_hallucination(self, 
                              unverified_claim: Dict[str, Any],
                              verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an unverified claim into taxonomy category.
        
        Args:
            unverified_claim: Claim that failed verification
            verification_results: Full verification report
        
        Returns:
            Classification with type, severity, and recommendations
        """
        claim_type = unverified_claim.get('type', 'unknown')
        reason = unverified_claim.get('reason', '')
        
        # Map claim type to hallucination type
        hallucination_type = self._map_claim_to_hallucination(claim_type, reason)
        
        taxonomy_entry = self.taxonomy.get(hallucination_type.value, {})
        
        return {
            'hallucination_type': hallucination_type.value,
            'category': taxonomy_entry.get('category', 'unknown'),
            'severity': taxonomy_entry.get('severity', 'unknown'),
            'description': taxonomy_entry.get('description', ''),
            'unverified_claim': unverified_claim,
            'confidence': self._calculate_classification_confidence(claim_type, reason)
        }
    
    def _map_claim_to_hallucination(self, claim_type: str, reason: str) -> HallucinationType:
        """Map verification failure to specific hallucination type."""
        if claim_type == 'instrument':
            if 'not found' in reason.lower():
                return HallucinationType.INSTRUMENT_NONEXISTENT
            else:
                return HallucinationType.INSTRUMENT_INCORRECT
        
        elif claim_type == 'step_order':
            return HallucinationType.STEP_ORDER_ERROR
        
        elif claim_type == 'anatomy':
            if 'location' in reason.lower():
                return HallucinationType.ANATOMICAL_LOCATION_ERROR
            else:
                return HallucinationType.ANATOMICAL_STRUCTURE_ERROR
        
        elif claim_type == 'complication':
            return HallucinationType.MANAGEMENT_ERROR
        
        else:
            return HallucinationType.NO_CITATION
    
    def _calculate_classification_confidence(self, claim_type: str, reason: str) -> float:
        """Calculate confidence in hallucination classification."""
        # High confidence for direct graph mismatches
        if 'not found' in reason.lower() or 'no graph relationship' in reason.lower():
            return 0.95
        # Medium confidence for inference-based classifications
        elif 'missing' in reason.lower():
            return 0.7
        # Lower confidence for ambiguous cases
        else:
            return 0.5
    
    def generate_error_report(self, 
                            verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive error analysis using taxonomy.
        
        Args:
            verification_results: Results from VerificationPipeline
        
        Returns:
            Detailed error report with:
            - Hallucinations by category
            - Severity distribution
            - Recommendations for improvement
        """
        unverified_details = verification_results.get('unverified_details', [])
        
        # Classify all unverified claims
        classifications = []
        for claim in unverified_details:
            classification = self.classify_hallucination(claim, verification_results)
            classifications.append(classification)
        
        # Aggregate by category
        category_counts = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for classification in classifications:
            category = classification['category']
            severity = classification['severity']
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_counts, severity_counts)
        
        return {
            'total_hallucinations': len(classifications),
            'classifications': classifications,
            'category_distribution': category_counts,
            'severity_distribution': severity_counts,
            'critical_count': severity_counts['critical'],
            'recommendations': recommendations,
            'safety_score': self._calculate_safety_score(severity_counts, len(classifications))
        }
    
    def _generate_recommendations(self, 
                                 category_counts: Dict[str, int],
                                 severity_counts: Dict[str, int]) -> List[str]:
        """Generate targeted recommendations based on error patterns."""
        recommendations = []
        
        # Critical severity triggers
        if severity_counts['critical'] > 0:
            recommendations.append("⚠️ CRITICAL: Manual review required before clinical use")
        
        # Category-specific recommendations
        if category_counts.get('anatomical', 0) > 0:
            recommendations.append("Enhance anatomy knowledge graph with more detailed relationships")
        
        if category_counts.get('instrument', 0) > 0:
            recommendations.append("Expand instrument-procedure mappings in knowledge graph")
        
        if category_counts.get('procedural', 0) > 0:
            recommendations.append("Add explicit step ordering constraints to graph")
        
        if category_counts.get('complication', 0) > 0:
            recommendations.append("Include comprehensive complication data in knowledge base")
        
        if category_counts.get('quantitative', 0) > 0:
            recommendations.append("Verify all numeric claims against original literature")
        
        return recommendations
    
    def _calculate_safety_score(self, severity_counts: Dict[str, int], total: int) -> float:
        """
        Calculate safety score (0-1, higher is safer).
        
        Weights:
        - Critical: -1.0 per occurrence
        - High: -0.5
        - Medium: -0.2
        - Low: -0.1
        """
        if total == 0:
            return 1.0
        
        penalty = (
            severity_counts['critical'] * 1.0 +
            severity_counts['high'] * 0.5 +
            severity_counts['medium'] * 0.2 +
            severity_counts['low'] * 0.1
        )
        
        # Normalize to 0-1 scale
        max_penalty = total * 1.0  # If all were critical
        safety_score = max(0.0, 1.0 - (penalty / max_penalty))
        
        return safety_score
    
    def get_taxonomy_summary(self) -> Dict[str, Any]:
        """Get complete taxonomy summary for documentation."""
        categories = {}
        for hallucination_type, details in self.taxonomy.items():
            category = details['category']
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'type': hallucination_type,
                'severity': details['severity'],
                'description': details['description']
            })
        
        return {
            'total_types': len(self.taxonomy),
            'categories': categories,
            'severity_levels': ['critical', 'high', 'medium', 'low']
        }
