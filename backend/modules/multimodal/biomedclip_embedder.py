"""
BiomedCLIP Embedder
Multimodal embeddings for surgical images and text using BiomedCLIP
Enables joint visual-semantic search for MICCAI research
"""

import torch
import open_clip
from typing import List, Union, Optional
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BiomedCLIPEmbedder:
    """
    BiomedCLIP-based multimodal embedder for surgical content.
    
    BiomedCLIP is a vision-language model trained on biomedical image-text pairs,
    making it ideal for surgical image understanding and retrieval.
    
    Paper: "BiomedCLIP: A Multimodal Biomedical Foundation Model" (2023)
    """
    
    def __init__(self, 
                 model_name: str = "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224",
                 device: Optional[str] = None):
        """
        Initialize BiomedCLIP embedder.
        
        Args:
            model_name: BiomedCLIP model identifier
            device: Device to run model on ('cuda', 'cpu', or None for auto-detect)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Loading BiomedCLIP on device: {self.device}")
        
        try:
            # Load BiomedCLIP model and preprocessing
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name,
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
            self.model.eval()  # Set to evaluation mode
            logger.info("✅ BiomedCLIP model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load BiomedCLIP: {e}")
            logger.info("Falling back to standard CLIP model")
            
            # Fallback to standard CLIP if BiomedCLIP unavailable
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32',
                pretrained='openai',
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
            self.model.eval()
            logger.info("✅ Standard CLIP model loaded as fallback")
    
    def embed_images(self, images: List[Union[str, Image.Image]]) -> np.ndarray:
        """
        Create embeddings for surgical images.
        
        Args:
            images: List of image paths or PIL Image objects
        
        Returns:
            numpy array of shape (num_images, embedding_dim)
        """
        processed_images = []
        
        for img in images:
            if isinstance(img, str):
                # Load from path
                img = Image.open(img).convert('RGB')
            
            # Preprocess image
            processed_img = self.preprocess(img).unsqueeze(0).to(self.device)
            processed_images.append(processed_img)
        
        # Stack all images
        image_batch = torch.cat(processed_images, dim=0)
        
        # Generate embeddings
        with torch.no_grad():
            image_features = self.model.encode_image(image_batch)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for text descriptions.
        
        Args:
            texts: List of text strings
        
        Returns:
            numpy array of shape (num_texts, embedding_dim)
        """
        # Tokenize texts
        text_tokens = self.tokenizer(texts).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features.cpu().numpy()
    
    def compute_similarity(self, 
                          images: Optional[List[Union[str, Image.Image]]] = None,
                          texts: Optional[List[str]] = None,
                          image_embeddings: Optional[np.ndarray] = None,
                          text_embeddings: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute similarity between images and texts.
        
        Args:
            images: List of images (if embeddings not provided)
            texts: List of texts (if embeddings not provided)
            image_embeddings: Pre-computed image embeddings
            text_embeddings: Pre-computed text embeddings
        
        Returns:
            Similarity matrix of shape (num_images, num_texts)
        """
        # Get embeddings if not provided
        if image_embeddings is None:
            if images is None:
                raise ValueError("Either images or image_embeddings must be provided")
            image_embeddings = self.embed_images(images)
        
        if text_embeddings is None:
            if texts is None:
                raise ValueError("Either texts or text_embeddings must be provided")
            text_embeddings = self.embed_texts(texts)
        
        # Compute cosine similarity
        similarity = image_embeddings @ text_embeddings.T
        
        return similarity
    
    def zero_shot_classification(self, 
                                 image: Union[str, Image.Image],
                                 categories: List[str],
                                 template: str = "A surgical image showing {}") -> dict:
        """
        Classify surgical image using zero-shot classification.
        
        Args:
            image: Image to classify
            categories: List of category labels
            template: Text template for categories
        
        Returns:
            Dictionary with categories and probabilities
        """
        # Create text descriptions
        texts = [template.format(cat) for cat in categories]
        
        # Get embeddings
        image_emb = self.embed_images([image])
        text_emb = self.embed_texts(texts)
        
        # Compute similarities
        similarities = (image_emb @ text_emb.T)[0]
        
        # Convert to probabilities
        probs = torch.nn.functional.softmax(torch.from_numpy(similarities) * 100, dim=0).numpy()
        
        # Create results
        results = {
            'predictions': [
                {'category': cat, 'probability': float(prob)}
                for cat, prob in zip(categories, probs)
            ],
            'top_prediction': categories[np.argmax(probs)],
            'confidence': float(np.max(probs))
        }
        
        return results
    
    def find_surgical_instruments(self, image: Union[str, Image.Image]) -> dict:
        """
        Identify surgical instruments in an image using zero-shot classification.
        
        Args:
            image: Surgical image
        
        Returns:
            Detected instruments with confidence scores
        """
        instruments = [
            'laparoscope',
            'trocar',
            'grasper',
            'scissors',
            'clip applier',
            'suction irrigator',
            'cautery device',
            'scalpel',
            'forceps',
            'retractor',
            'needle holder',
            'stapler'
        ]
        
        return self.zero_shot_classification(
            image,
            instruments,
            template="A surgical image showing a {}"
        )
    
    def identify_surgical_phase(self, image: Union[str, Image.Image]) -> dict:
        """
        Identify surgical phase from image.
        
        Args:
            image: Surgical image
        
        Returns:
            Surgical phase classification
        """
        phases = [
            'initial access and port placement',
            'dissection and exposure',
            'critical view of safety',
            'clipping and cutting',
            'specimen extraction',
            'hemostasis and irrigation',
            'closure'
        ]
        
        return self.zero_shot_classification(
            image,
            phases,
            template="Surgical phase: {}"
        )
    
    def get_embedding_dim(self) -> int:
        """Get the dimensionality of embeddings."""
        return self.model.visual.output_dim
