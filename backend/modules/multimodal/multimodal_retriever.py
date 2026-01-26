"""
Multimodal Retriever for MICCAI Research
Combines text, image, and graph-based retrieval for comprehensive surgical knowledge retrieval
"""

from typing import List, Dict, Any, Optional, Union
import numpy as np
from PIL import Image
import logging

from .biomedclip_embedder import BiomedCLIPEmbedder
from .multimodal_kg_manager import MultimodalKGManager
from ..retriever.faiss_manager import FaissManager
from ..graph.entity_extractor import MedicalEntityExtractor

logger = logging.getLogger(__name__)


class MultimodalRetriever:
    """
    Advanced multimodal retrieval combining:
    1. Text retrieval (FAISS + BioClinicalBERT)
    2. Image retrieval (BiomedCLIP visual embeddings)
    3. Graph traversal (Neo4j multimodal knowledge graph)
    4. Cross-modal retrieval (text->image, image->text)
    
    This enables:
    - Visual Question Answering about surgical images
    - Finding relevant images for text queries
    - Finding relevant text for image queries
    - Graph-enhanced multimodal understanding
    
    Novel contribution for MICCAI:
    - Joint visual-semantic surgical knowledge retrieval
    - Automated multimodal knowledge graph construction
    - Zero-shot surgical instrument/phase recognition
    """
    
    def __init__(self,
                 text_embedder,  # BioClinicalEmbedder
                 visual_embedder: BiomedCLIPEmbedder,
                 faiss_manager: FaissManager,
                 kg_manager: MultimodalKGManager,
                 entity_extractor: MedicalEntityExtractor,
                 text_weight: float = 0.4,
                 visual_weight: float = 0.3,
                 graph_weight: float = 0.3):
        """
        Initialize multimodal retriever.
        
        Args:
            text_embedder: BioClinicalBERT embedder
            visual_embedder: BiomedCLIP embedder
            faiss_manager: Vector store for text
            kg_manager: Multimodal knowledge graph
            entity_extractor: Medical entity extractor
            text_weight: Weight for text similarity
            visual_weight: Weight for visual similarity
            graph_weight: Weight for graph relevance
        """
        self.text_embedder = text_embedder
        self.visual_embedder = visual_embedder
        self.faiss = faiss_manager
        self.kg = kg_manager
        self.extractor = entity_extractor
        
        # Normalize weights
        total = text_weight + visual_weight + graph_weight
        self.text_weight = text_weight / total
        self.visual_weight = visual_weight / total
        self.graph_weight = graph_weight / total
        
        logger.info(f"Initialized multimodal retriever (text: {self.text_weight:.2f}, "
                   f"visual: {self.visual_weight:.2f}, graph: {self.graph_weight:.2f})")
    
    def retrieve_multimodal(self,
                           text_query: Optional[str] = None,
                           image_query: Optional[Union[str, Image.Image]] = None,
                           top_k: int = 5,
                           return_images: bool = True,
                           return_text: bool = True) -> List[Dict[str, Any]]:
        """
        Unified multimodal retrieval supporting text, image, or both.
        
        Args:
            text_query: Text query (optional)
            image_query: Image query path or PIL Image (optional)
            top_k: Number of results
            return_images: Include image results
            return_text: Include text results
        
        Returns:
            List of multimodal results with text, images, and scores
        """
        if not text_query and not image_query:
            raise ValueError("At least one of text_query or image_query must be provided")
        
        results = []
        
        # 1. Text-based retrieval
        if text_query and return_text:
            text_results = self._text_retrieval(text_query, top_k)
            results.extend(text_results)
        
        # 2. Image-based retrieval
        if image_query:
            image_results = self._image_retrieval(image_query, top_k, return_images, return_text)
            results.extend(image_results)
        
        # 3. Cross-modal retrieval (text->images, image->text)
        if text_query and image_query is None and return_images:
            cross_modal_images = self._text_to_image_retrieval(text_query, top_k)
            results.extend(cross_modal_images)
        
        # 4. Graph-enhanced retrieval
        if text_query:
            entities = self.extractor.extract_entities(text_query)
            graph_results = self._graph_multimodal_retrieval(entities, top_k)
            results.extend(graph_results)
        
        # Merge and rank results
        merged = self._merge_multimodal_results(results, top_k)
        
        return merged
    
    def visual_qa(self,
                  image: Union[str, Image.Image],
                  question: str,
                  use_graph: bool = True) -> Dict[str, Any]:
        """
        Answer questions about surgical images.
        
        Examples:
        - "What instruments are visible in this image?"
        - "What surgical phase is shown?"
        - "What anatomical structures are visible?"
        
        Args:
            image: Surgical image
            question: Question about the image
            use_graph: Use knowledge graph for context
        
        Returns:
            Answer with confidence and supporting evidence
        """
        # Get visual embedding
        visual_emb = self.visual_embedder.embed_images([image])[0]
        
        # Get text embedding of question
        question_emb = self.text_embedder.embed_texts([question])[0]
        
        # Analyze image content
        answer_parts = []
        confidence_scores = []
        
        # 1. Detect instruments
        if 'instrument' in question.lower():
            instruments = self.visual_embedder.find_surgical_instruments(image)
            top_instruments = [
                p for p in instruments['predictions']
                if p['probability'] > 0.1
            ]
            
            if top_instruments:
                inst_names = [p['category'] for p in top_instruments[:3]]
                answer_parts.append(f"Visible instruments: {', '.join(inst_names)}")
                confidence_scores.append(instruments['confidence'])
        
        # 2. Identify surgical phase
        if 'phase' in question.lower() or 'step' in question.lower():
            phases = self.visual_embedder.identify_surgical_phase(image)
            answer_parts.append(f"Surgical phase: {phases['top_prediction']}")
            confidence_scores.append(phases['confidence'])
        
        # 3. Use graph context
        if use_graph:
            # Find similar images in graph
            similar_images = self.kg.find_similar_images(visual_emb.tolist(), top_k=3)
            
            if similar_images:
                # Get context from similar images
                contexts = []
                for sim_img in similar_images:
                    ctx = self.kg.get_image_context(sim_img['image_id'])
                    if ctx:
                        contexts.append(ctx)
                
                # Extract procedures and anatomy
                procedures = set()
                anatomy = set()
                for ctx in contexts:
                    procedures.update([p['name'] for p in ctx.get('procedures', [])])
                    anatomy.update([a['name'] for a in ctx.get('anatomy', [])])
                
                if procedures:
                    answer_parts.append(f"Related procedures: {', '.join(list(procedures)[:3])}")
                if anatomy:
                    answer_parts.append(f"Anatomical structures: {', '.join(list(anatomy)[:3])}")
        
        # Combine answer
        if answer_parts:
            answer = ". ".join(answer_parts)
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        else:
            answer = "Unable to identify specific elements in the image."
            avg_confidence = 0.0
        
        return {
            'question': question,
            'answer': answer,
            'confidence': float(avg_confidence),
            'method': 'multimodal_visual_qa'
        }
    
    def find_images_for_text(self, text_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find surgical images relevant to text query.
        Cross-modal retrieval: text -> images
        
        Args:
            text_query: Text description
            top_k: Number of images
        
        Returns:
            List of relevant images with scores
        """
        return self._text_to_image_retrieval(text_query, top_k)
    
    def find_text_for_image(self, image: Union[str, Image.Image], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find text descriptions relevant to image.
        Cross-modal retrieval: image -> text
        
        Args:
            image: Surgical image
            top_k: Number of text results
        
        Returns:
            List of relevant text with scores
        """
        # Get visual embedding
        visual_emb = self.visual_embedder.embed_images([image])[0]
        
        # Convert to text embedding space using CLIP's joint space
        # In practice, use the visual embedding directly for cross-modal search
        
        # Find similar images in graph
        similar_images = self.kg.find_similar_images(visual_emb.tolist(), top_k=10)
        
        # Get procedures/text associated with similar images
        results = []
        for sim_img in similar_images:
            ctx = self.kg.get_image_context(sim_img['image_id'])
            if ctx:
                for proc in ctx.get('procedures', []):
                    results.append({
                        'text': f"Procedure: {proc['name']}",
                        'score': sim_img['similarity'] * proc.get('confidence', 1.0),
                        'source': 'image_to_text',
                        'image_id': sim_img['image_id']
                    })
        
        # Sort and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _text_retrieval(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve text documents using FAISS."""
        query_emb = self.text_embedder.embed_texts([query])[0]
        results = self.faiss.query(query_emb, top_k=top_k)
        
        for r in results:
            r['modality'] = 'text'
            r['retrieval_method'] = 'faiss_text'
            r['weight'] = self.text_weight
        
        return results
    
    def _image_retrieval(self,
                        image: Union[str, Image.Image],
                        top_k: int,
                        return_images: bool,
                        return_text: bool) -> List[Dict[str, Any]]:
        """Retrieve similar images from knowledge graph."""
        visual_emb = self.visual_embedder.embed_images([image])[0]
        
        similar_images = self.kg.find_similar_images(visual_emb.tolist(), top_k=top_k)
        
        results = []
        for img in similar_images:
            result = {
                'image_id': img['image_id'],
                'image_path': img['path'],
                'score': img['similarity'],
                'modality': 'image',
                'retrieval_method': 'visual_similarity',
                'weight': self.visual_weight
            }
            
            # Add context if needed
            if return_text:
                ctx = self.kg.get_image_context(img['image_id'])
                if ctx:
                    result['context'] = ctx
            
            results.append(result)
        
        return results
    
    def _text_to_image_retrieval(self, text_query: str, top_k: int) -> List[Dict[str, Any]]:
        """Cross-modal: find images for text query."""
        # Get text embedding in CLIP space
        text_emb = self.visual_embedder.embed_texts([text_query])[0]
        
        # Find similar images
        similar_images = self.kg.find_similar_images(text_emb.tolist(), top_k=top_k, threshold=0.2)
        
        results = []
        for img in similar_images:
            results.append({
                'image_id': img['image_id'],
                'image_path': img['path'],
                'score': img['similarity'],
                'modality': 'image',
                'retrieval_method': 'cross_modal_text_to_image',
                'weight': self.visual_weight
            })
        
        return results
    
    def _graph_multimodal_retrieval(self, entities: Dict[str, List[str]], top_k: int) -> List[Dict[str, Any]]:
        """Retrieve both text and images from knowledge graph."""
        results = []
        
        procedures = entities.get('procedures', [])
        
        for proc in procedures[:2]:
            # Get images for procedure
            images = self.kg.get_images_for_procedure(proc, min_confidence=0.5)
            
            for img in images[:top_k]:
                results.append({
                    'image_id': img['image_id'],
                    'image_path': img['path'],
                    'score': img['confidence'],
                    'procedure': proc,
                    'modality': 'image',
                    'retrieval_method': 'graph_traversal',
                    'weight': self.graph_weight
                })
        
        return results
    
    def _merge_multimodal_results(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Merge and rank multimodal results."""
        # Apply weights
        for r in results:
            weight = r.get('weight', 1.0)
            r['final_score'] = r.get('score', 0.0) * weight
        
        # Remove duplicates
        unique_results = []
        seen_ids = set()
        
        for r in results:
            # Create unique key
            if 'image_id' in r:
                key = f"img_{r['image_id']}"
            elif 'text' in r:
                key = f"text_{r['text'][:50]}"
            else:
                key = str(hash(str(r)))
            
            if key not in seen_ids:
                seen_ids.add(key)
                unique_results.append(r)
        
        # Sort by final score
        unique_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return unique_results[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get multimodal system statistics."""
        return {
            'knowledge_graph': self.kg.get_multimodal_statistics(),
            'weights': {
                'text': self.text_weight,
                'visual': self.visual_weight,
                'graph': self.graph_weight
            },
            'capabilities': [
                'text_retrieval',
                'image_retrieval',
                'visual_qa',
                'cross_modal_retrieval',
                'graph_traversal'
            ]
        }
