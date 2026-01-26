"""
Multimodal Knowledge Graph Manager
Extends Neo4j manager with image node support for MICCAI research
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


class MultimodalKGManager:
    """
    Manages multimodal knowledge graph with surgical images.
    
    New Node Types (in addition to text-only):
    - SurgicalImage: Image nodes with visual embeddings
    - VideoFrame: Extracted video frames
    - VisualConcept: Visual concepts detected in images
    
    New Relationship Types:
    - DEPICTS: Image -> Procedure/Anatomy/Instrument
    - SHOWS_PHASE: Image -> SurgicalPhase
    - CAPTURED_DURING: Image -> Procedure
    - SIMILAR_TO: Image -> Image
    - ILLUSTRATES: Image -> TextChunk
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize multimodal graph database."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connectivity()
        self._create_multimodal_indexes()
    
    def _verify_connectivity(self):
        """Verify database connection."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Connected to multimodal Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_multimodal_indexes(self):
        """Create indexes for multimodal nodes."""
        indexes = [
            # Original indexes
            "CREATE INDEX procedure_name IF NOT EXISTS FOR (p:Procedure) ON (p.name)",
            "CREATE INDEX anatomy_name IF NOT EXISTS FOR (a:Anatomy) ON (a.name)",
            "CREATE INDEX instrument_name IF NOT EXISTS FOR (i:Instrument) ON (i.name)",
            "CREATE INDEX complication_name IF NOT EXISTS FOR (c:Complication) ON (c.name)",
            "CREATE INDEX technique_name IF NOT EXISTS FOR (t:Technique) ON (t.name)",
            "CREATE INDEX medication_name IF NOT EXISTS FOR (m:Medication) ON (m.name)",
            # Multimodal indexes
            "CREATE INDEX image_id IF NOT EXISTS FOR (img:SurgicalImage) ON (img.image_id)",
            "CREATE INDEX frame_id IF NOT EXISTS FOR (f:VideoFrame) ON (f.frame_id)",
            "CREATE INDEX phase_name IF NOT EXISTS FOR (ph:SurgicalPhase) ON (ph.name)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
        
        logger.info("Multimodal graph indexes created")
    
    def create_image_node(self,
                         image_id: str,
                         image_path: str,
                         embedding: List[float],
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create surgical image node with visual embedding.
        
        Args:
            image_id: Unique image identifier
            image_path: Path to image file
            embedding: Visual embedding vector from BiomedCLIP
            metadata: Quality metrics, dimensions, etc.
        
        Returns:
            Node ID
        """
        meta = metadata or {}
        
        with self.driver.session() as session:
            result = session.run("""
                CREATE (img:SurgicalImage {
                    image_id: $image_id,
                    path: $image_path,
                    embedding: $embedding,
                    width: $width,
                    height: $height,
                    quality_score: $quality_score,
                    created_at: datetime()
                })
                RETURN elementId(img) as id
            """, 
                image_id=image_id,
                image_path=image_path,
                embedding=embedding,
                width=meta.get('width', 0),
                height=meta.get('height', 0),
                quality_score=meta.get('quality_score', 0.0)
            )
            
            node_id = result.single()['id']
            logger.debug(f"Created image node: {image_id}")
            return node_id
    
    def create_video_frame_node(self,
                               frame_id: str,
                               video_path: str,
                               timestamp: float,
                               frame_number: int,
                               embedding: List[float],
                               phase_index: Optional[int] = None) -> str:
        """
        Create video frame node.
        
        Args:
            frame_id: Unique frame identifier
            video_path: Source video path
            timestamp: Time in video (seconds)
            frame_number: Frame number in video
            embedding: Visual embedding
            phase_index: Surgical phase index
        
        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run("""
                CREATE (f:VideoFrame {
                    frame_id: $frame_id,
                    video_path: $video_path,
                    timestamp: $timestamp,
                    frame_number: $frame_number,
                    embedding: $embedding,
                    phase_index: $phase_index,
                    created_at: datetime()
                })
                RETURN elementId(f) as id
            """,
                frame_id=frame_id,
                video_path=video_path,
                timestamp=timestamp,
                frame_number=frame_number,
                embedding=embedding,
                phase_index=phase_index
            )
            
            return result.single()['id']
    
    def create_surgical_phase_node(self, name: str, description: str = "") -> str:
        """Create or merge surgical phase node."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (ph:SurgicalPhase {name: $name})
                ON CREATE SET 
                    ph.description = $description,
                    ph.created_at = datetime()
                RETURN elementId(ph) as id
            """, name=name, description=description)
            
            return result.single()['id']
    
    def link_image_to_procedure(self, image_id: str, procedure_name: str, confidence: float = 1.0):
        """Link image to procedure with confidence score."""
        with self.driver.session() as session:
            session.run("""
                MATCH (img:SurgicalImage {image_id: $image_id})
                MATCH (p:Procedure {name: $procedure_name})
                MERGE (img)-[r:DEPICTS]->(p)
                SET r.confidence = $confidence
            """, image_id=image_id, procedure_name=procedure_name, confidence=confidence)
    
    def link_image_to_instrument(self, image_id: str, instrument_name: str, confidence: float):
        """Link image to surgical instrument."""
        with self.driver.session() as session:
            session.run("""
                MATCH (img:SurgicalImage {image_id: $image_id})
                MERGE (i:Instrument {name: $instrument_name})
                MERGE (img)-[r:SHOWS_INSTRUMENT]->(i)
                SET r.confidence = $confidence
            """, image_id=image_id, instrument_name=instrument_name, confidence=confidence)
    
    def link_image_to_anatomy(self, image_id: str, anatomy_name: str, confidence: float):
        """Link image to anatomical structure."""
        with self.driver.session() as session:
            session.run("""
                MATCH (img:SurgicalImage {image_id: $image_id})
                MERGE (a:Anatomy {name: $anatomy_name})
                MERGE (img)-[r:SHOWS_ANATOMY]->(a)
                SET r.confidence = $confidence
            """, image_id=image_id, anatomy_name=anatomy_name, confidence=confidence)
    
    def link_frame_to_phase(self, frame_id: str, phase_name: str, confidence: float):
        """Link video frame to surgical phase."""
        with self.driver.session() as session:
            session.run("""
                MATCH (f:VideoFrame {frame_id: $frame_id})
                MATCH (ph:SurgicalPhase {name: $phase_name})
                MERGE (f)-[r:IN_PHASE]->(ph)
                SET r.confidence = $confidence
            """, frame_id=frame_id, phase_name=phase_name, confidence=confidence)
    
    def find_similar_images(self, embedding: List[float], top_k: int = 5, threshold: float = 0.7) -> List[Dict]:
        """
        Find similar images using cosine similarity (approximate).
        
        Note: For production, use vector index (available in Neo4j 5.11+)
        
        Args:
            embedding: Query image embedding
            top_k: Number of results
            threshold: Similarity threshold
        
        Returns:
            List of similar images with scores
        """
        with self.driver.session() as session:
            # Note: This is a simplified version
            # For production, use Neo4j vector index for efficient similarity search
            result = session.run("""
                MATCH (img:SurgicalImage)
                RETURN img.image_id as image_id,
                       img.path as path,
                       img.embedding as embedding
                LIMIT 1000
            """)
            
            results = []
            query_emb = embedding
            
            for record in result:
                img_emb = record['embedding']
                
                # Compute cosine similarity
                dot_product = sum(a * b for a, b in zip(query_emb, img_emb))
                norm_query = sum(a * a for a in query_emb) ** 0.5
                norm_img = sum(b * b for b in img_emb) ** 0.5
                
                if norm_query > 0 and norm_img > 0:
                    similarity = dot_product / (norm_query * norm_img)
                    
                    if similarity >= threshold:
                        results.append({
                            'image_id': record['image_id'],
                            'path': record['path'],
                            'similarity': similarity
                        })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    def get_image_context(self, image_id: str) -> Dict[str, Any]:
        """
        Get full context for a surgical image.
        
        Returns:
            Dictionary with procedures, instruments, anatomy shown
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (img:SurgicalImage {image_id: $image_id})
                OPTIONAL MATCH (img)-[d:DEPICTS]->(p:Procedure)
                OPTIONAL MATCH (img)-[si:SHOWS_INSTRUMENT]->(i:Instrument)
                OPTIONAL MATCH (img)-[sa:SHOWS_ANATOMY]->(a:Anatomy)
                OPTIONAL MATCH (img)-[ip:IN_PHASE]->(ph:SurgicalPhase)
                RETURN img,
                       collect(DISTINCT {name: p.name, confidence: d.confidence}) as procedures,
                       collect(DISTINCT {name: i.name, confidence: si.confidence}) as instruments,
                       collect(DISTINCT {name: a.name, confidence: sa.confidence}) as anatomy,
                       collect(DISTINCT {name: ph.name, confidence: ip.confidence}) as phases
            """, image_id=image_id)
            
            record = result.single()
            
            if not record:
                return None
            
            return {
                'image_id': image_id,
                'path': record['img']['path'],
                'procedures': [p for p in record['procedures'] if p['name']],
                'instruments': [i for i in record['instruments'] if i['name']],
                'anatomy': [a for a in record['anatomy'] if a['name']],
                'phases': [ph for ph in record['phases'] if ph['name']]
            }
    
    def get_images_for_procedure(self, procedure_name: str, min_confidence: float = 0.5) -> List[Dict]:
        """Get all images depicting a procedure."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (img:SurgicalImage)-[d:DEPICTS]->(p:Procedure {name: $procedure_name})
                WHERE d.confidence >= $min_confidence
                RETURN img.image_id as image_id,
                       img.path as path,
                       d.confidence as confidence
                ORDER BY d.confidence DESC
            """, procedure_name=procedure_name, min_confidence=min_confidence)
            
            return [dict(record) for record in result]
    
    def get_multimodal_statistics(self) -> Dict[str, Any]:
        """Get statistics about the multimodal knowledge graph."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN 
                    count(n) as total_nodes,
                    count(DISTINCT labels(n)) as node_types,
                    size([(n)-[r]->() | r]) as total_relationships
            """)
            
            stats = dict(result.single())
            
            # Count specific node types
            type_counts = session.run("""
                MATCH (img:SurgicalImage) RETURN count(img) as images
                UNION ALL
                MATCH (f:VideoFrame) RETURN count(f) as frames
                UNION ALL
                MATCH (p:Procedure) RETURN count(p) as procedures
                UNION ALL
                MATCH (i:Instrument) RETURN count(i) as instruments
            """)
            
            stats['breakdown'] = [dict(record) for record in type_counts]
            
            return stats
    
    def close(self):
        """Close database connection."""
        self.driver.close()
        logger.info("Neo4j connection closed")
