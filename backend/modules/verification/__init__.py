"""
Verification Module
Graph-based answer verification system with hallucination taxonomy and abstention.
"""

from .verification_pipeline import VerificationPipeline
from .surgical_hallucination_taxonomy import SurgicalHallucinationTaxonomy, HallucinationType
from .abstention_policy import AbstentionPolicy, UncertaintyQuantifier, should_abstain_from_answer

__all__ = [
    'VerificationPipeline',
    'SurgicalHallucinationTaxonomy',
    'HallucinationType',
    'AbstentionPolicy',
    'UncertaintyQuantifier',
    'should_abstain_from_answer'
]
