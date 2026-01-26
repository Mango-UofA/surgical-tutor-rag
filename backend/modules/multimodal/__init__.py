"""
Multimodal RAG Module
Combines visual and textual information using BiomedCLIP for MICCAI-worthy research
"""

from .biomedclip_embedder import BiomedCLIPEmbedder
from .image_processor import SurgicalImageProcessor
from .multimodal_retriever import MultimodalRetriever

__all__ = [
    'BiomedCLIPEmbedder',
    'SurgicalImageProcessor',
    'MultimodalRetriever'
]
