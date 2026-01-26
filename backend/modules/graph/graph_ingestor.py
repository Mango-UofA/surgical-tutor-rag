"""
Graph-Enhanced PDF Ingestion Pipeline
Processes PDFs to extract both:
1. Text chunks for vector embeddings (FAISS)
2. Medical entities for knowledge graph (Neo4j)
"""

from typing import List, Dict, Any, Optional
import logging
from ..data_ingestion.pdf_parser import extract_text_from_pdf_bytes
from ..data_ingestion.chunker import chunk_text
from ..embedder.embedder import BioClinicalBERTEmbedder
from ..retriever.faiss_manager import FAISSManager
from ..graph.neo4j_manager import Neo4jManager
from ..graph.entity_extractor import MedicalEntityExtractor

logger = logging.getLogger(__name__)


class GraphEnhancedIngestor:
    """
    Enhanced document ingestion that builds both vector index and knowledge graph.
    """
    
    def __init__(self,
                 embedder: BioClinicalBERTEmbedder,
                 faiss_manager: FAISSManager,
                 neo4j_manager: Optional[Neo4jManager] = None,
                 entity_extractor: Optional[MedicalEntityExtractor] = None,
                 build_graph: bool = True):
        """
        Initialize the graph-enhanced ingestor.
        
        Args:
            embedder: Text embedding model
            faiss_manager: Vector store manager
            neo4j_manager: Graph database manager (optional)
            entity_extractor: Medical entity extractor (optional)
            build_graph: Whether to build knowledge graph during ingestion
        """
        self.embedder = embedder
        self.faiss = faiss_manager
        self.graph = neo4j_manager
        self.extractor = entity_extractor
        self.build_graph = build_graph and (neo4j_manager is not None) and (entity_extractor is not None)
        
        if self.build_graph:
            logger.info("Graph-enhanced ingestion enabled")
        else:
            logger.info("Graph-enhanced ingestion disabled (vector-only mode)")
    
    def ingest_pdf(self, 
                   pdf_bytes: bytes, 
                   filename: str,
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ingest a PDF document into both vector store and knowledge graph.
        
        Args:
            pdf_bytes: PDF file bytes
            filename: Original filename
            metadata: Additional metadata
        
        Returns:
            Ingestion statistics
        """
        stats = {
            'filename': filename,
            'chunks_created': 0,
            'embeddings_added': 0,
            'entities_extracted': 0,
            'graph_nodes_created': 0,
            'graph_relationships_created': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Step 1: Extract text from PDF
            logger.info(f"Extracting text from {filename}")
            full_text = extract_text_from_pdf_bytes(pdf_bytes)
            
            if not full_text.strip():
                raise ValueError("No text extracted from PDF")
            
            # Step 2: Chunk text for vector embeddings
            logger.info("Chunking text")
            chunks = chunk_text(full_text)
            stats['chunks_created'] = len(chunks)
            
            # Step 3: Create embeddings and add to FAISS
            logger.info(f"Creating embeddings for {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                embedding = self.embedder.embed_text(chunk)
                chunk_metadata = {
                    'source': filename,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    **(metadata or {})
                }
                self.faiss.add_document(chunk, embedding, chunk_metadata)
            
            stats['embeddings_added'] = len(chunks)
            
            # Step 4: Build knowledge graph (if enabled)
            if self.build_graph:
                logger.info("Building knowledge graph from document")
                graph_stats = self._build_graph_from_text(full_text, filename)
                stats.update(graph_stats)
            
            stats['success'] = True
            logger.info(f"Successfully ingested {filename}: {stats['chunks_created']} chunks, "
                       f"{stats['entities_extracted']} entities")
        
        except Exception as e:
            logger.error(f"Failed to ingest {filename}: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _build_graph_from_text(self, text: str, source: str) -> Dict[str, Any]:
        """
        Extract entities and build knowledge graph from text.
        
        Args:
            text: Full document text
            source: Document source/filename
        
        Returns:
            Graph building statistics
        """
        stats = {
            'entities_extracted': 0,
            'graph_nodes_created': 0,
            'graph_relationships_created': 0
        }
        
        try:
            # Extract entities from the entire document
            logger.info("Extracting medical entities")
            entities = self.extractor.extract_entities(text)
            
            # Count total entities
            total_entities = sum(len(v) for v in entities.values())
            stats['entities_extracted'] = total_entities
            
            if total_entities == 0:
                logger.warning("No entities extracted from document")
                return stats
            
            # Identify main procedures in the document
            main_procedures = self.extractor.identify_main_procedures(text, top_n=5)
            
            logger.info(f"Found {len(main_procedures)} main procedures: {[p[0] for p in main_procedures]}")
            
            # For each main procedure, build graph
            for procedure_name, frequency in main_procedures:
                # Extract procedure-specific entities
                proc_entities = self.extractor.extract_procedure_specific_entities(text, procedure_name)
                
                # Add procedure and related entities to graph
                self.graph.add_procedure_with_entities(procedure_name, proc_entities)
                
                # Count nodes (approximate - some may be duplicates)
                stats['graph_nodes_created'] += 1 + sum(len(v) for v in proc_entities.values())
                stats['graph_relationships_created'] += sum(len(v) for v in proc_entities.values())
            
            # Extract and add relationships
            relationships = self.extractor.extract_relationships(text)
            logger.info(f"Extracted {len(relationships)} relationships from text")
            
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
        
        return stats
    
    def ingest_multiple_pdfs(self, 
                            pdf_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ingest multiple PDFs in batch.
        
        Args:
            pdf_files: List of dicts with 'bytes', 'filename', and optional 'metadata'
        
        Returns:
            List of ingestion statistics for each file
        """
        results = []
        
        for i, pdf_file in enumerate(pdf_files):
            logger.info(f"Ingesting file {i+1}/{len(pdf_files)}: {pdf_file['filename']}")
            
            stats = self.ingest_pdf(
                pdf_file['bytes'],
                pdf_file['filename'],
                pdf_file.get('metadata', {})
            )
            results.append(stats)
        
        # Log summary
        successful = sum(1 for r in results if r['success'])
        total_chunks = sum(r['chunks_created'] for r in results)
        total_entities = sum(r['entities_extracted'] for r in results)
        
        logger.info(f"Batch ingestion complete: {successful}/{len(pdf_files)} successful, "
                   f"{total_chunks} total chunks, {total_entities} total entities")
        
        return results
    
    def get_ingestion_summary(self) -> Dict[str, Any]:
        """
        Get summary of ingested data.
        
        Returns:
            Summary statistics
        """
        summary = {
            'vector_store': {
                'total_documents': self.faiss.get_index_size()
            }
        }
        
        if self.build_graph:
            summary['knowledge_graph'] = self.graph.get_graph_statistics()
        
        return summary
