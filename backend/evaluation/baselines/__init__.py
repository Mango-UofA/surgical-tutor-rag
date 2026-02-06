"""
Initialization file for baselines module
"""

from .baseline_systems import (
    BM25Retriever,
    OpenAIEmbeddingRetriever,
    VanillaGPTBaseline,
    DenseRetrievalBaseline,
    compare_baselines
)

__all__ = [
    'BM25Retriever',
    'OpenAIEmbeddingRetriever',
    'VanillaGPTBaseline',
    'DenseRetrievalBaseline',
    'compare_baselines'
]
