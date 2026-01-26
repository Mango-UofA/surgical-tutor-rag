import os
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Union
from PIL import Image

from app.config import (
    BIOCLINICALBERT_MODEL, CHUNK_TOKEN_TARGET, FAISS_INDEX_PATH,
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, SCISPACY_MODEL
)
from app.db import get_db
from modules.data_ingestion.pdf_parser import extract_text_from_pdf_bytes
from modules.data_ingestion.chunker import simple_chunk_text
from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
from modules.generator.generator import Generator
from modules.quiz_generator.quiz_generator import QuizGenerator

# Graph-enhanced modules (optional - gracefully handle if dependencies missing)
try:
    from modules.graph.neo4j_manager import Neo4jManager
    from modules.graph.entity_extractor import MedicalEntityExtractor
    from modules.graph.graph_retriever import GraphEnhancedRetriever
    from modules.graph.graph_ingestor import GraphEnhancedIngestor
    GRAPH_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Graph features unavailable (missing dependencies): {e}")
    print("⚠️  Continuing with vector-only mode")
    Neo4jManager = None
    MedicalEntityExtractor = None
    GraphEnhancedRetriever = None
    GraphEnhancedIngestor = None
    GRAPH_IMPORTS_AVAILABLE = False

# Multimodal modules
try:
    from modules.multimodal.biomedclip_embedder import BiomedCLIPEmbedder
    from modules.multimodal.image_processor import SurgicalImageProcessor
    from modules.multimodal.multimodal_kg_manager import MultimodalKGManager
    from modules.multimodal.multimodal_retriever import MultimodalRetriever
    from modules.storage.image_storage import ImageStorageManager
    MULTIMODAL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Multimodal features unavailable: {e}")
    print("⚠️  Install with: pip install open-clip-torch pillow opencv-python")
    BiomedCLIPEmbedder = None
    SurgicalImageProcessor = None
    MultimodalKGManager = None
    ImageStorageManager = None
    MultimodalRetriever = None
    MULTIMODAL_AVAILABLE = False

app = FastAPI(title="Surgical Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize embedder and faiss manager lazily
_embedder: Optional[BioClinicalEmbedder] = None
_faiss: Optional[FaissManager] = None
_gen: Optional[Generator] = None
_quiz: Optional[QuizGenerator] = None

# Graph-enhanced components
_neo4j = None
_entity_extractor = None
_graph_retriever = None
_graph_ingestor = None
_graph_enabled: bool = False

# Multimodal components
_biomedclip = None
_image_processor = None
_multimodal_kg = None
_multimodal_retriever = None
_image_storage = None
_multimodal_enabled: bool = False


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = BioClinicalEmbedder(BIOCLINICALBERT_MODEL)
    return _embedder


def get_faiss():
    global _faiss
    if _faiss is None:
        embedder = get_embedder()
        dim = embedder.dim()
        _faiss = FaissManager(dim=dim, index_path=FAISS_INDEX_PATH)
        # try to load existing
        try:
            _faiss.load(FAISS_INDEX_PATH)
        except Exception:
            pass
    return _faiss


def get_generator():
    global _gen
    if _gen is None:
        _gen = Generator()
    return _gen


def get_quiz():
    global _quiz
    if _quiz is None:
        _quiz = QuizGenerator()
    return _quiz


def get_neo4j():
    """Get Neo4j manager (returns None if connection fails)"""
    global _neo4j, _graph_enabled
    
    if not GRAPH_IMPORTS_AVAILABLE:
        return None
        
    if _neo4j is None and not _graph_enabled:
        try:
            _neo4j = Neo4jManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            _graph_enabled = True
            print("✅ Neo4j connection established - Graph features enabled")
        except Exception as e:
            print(f"⚠️  Neo4j connection failed: {e}")
            print("⚠️  Continuing with vector-only mode (graph features disabled)")
            _graph_enabled = False
    return _neo4j


def get_entity_extractor():
    """Get medical entity extractor (returns None if model loading fails)"""
    global _entity_extractor
    
    if not GRAPH_IMPORTS_AVAILABLE:
        return None
        
    if _entity_extractor is None:
        try:
            _entity_extractor = MedicalEntityExtractor(SCISPACY_MODEL)
            print("✅ Medical entity extractor loaded")
        except Exception as e:
            print(f"⚠️  Entity extractor failed to load: {e}")
            print("⚠️  Install with: pip install scispacy && pip install en_core_sci_md")
    return _entity_extractor


def get_graph_retriever():
    """Get graph-enhanced retriever (falls back to FAISS-only if graph unavailable)"""
    global _graph_retriever
    if _graph_retriever is None:
        neo4j = get_neo4j()
        extractor = get_entity_extractor()
        faiss = get_faiss()
        embedder = get_embedder()
        
        if neo4j and extractor:
            _graph_retriever = GraphEnhancedRetriever(
                faiss, neo4j, extractor, embedder,
                vector_weight=0.6, graph_weight=0.4
            )
            print("✅ Graph-enhanced retriever initialized")
        else:
            print("⚠️  Graph retriever unavailable - using FAISS-only mode")
    return _graph_retriever


def get_graph_ingestor():
    """Get graph-enhanced ingestor"""
    global _graph_ingestor
    if _graph_ingestor is None:
        embedder = get_embedder()
        faiss = get_faiss()
        neo4j = get_neo4j()
        extractor = get_entity_extractor()
        
        _graph_ingestor = GraphEnhancedIngestor(
            embedder, faiss, neo4j, extractor,
            build_graph=(neo4j is not None and extractor is not None)
        )
    return _graph_ingestor


def is_graph_enabled():
    """Check if graph features are available"""
    get_neo4j()  # Initialize if needed
    return _graph_enabled


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    """Check system status and index statistics"""
    faiss = get_faiss()
    
    status_data = {
        "status": "ok",
        "vectors_in_index": faiss.index.ntotal,
        "documents_indexed": len(set(meta.get("source") for meta in faiss.id_to_meta.values())),
        "total_chunks": len(faiss.id_to_meta),
        "graph_enabled": is_graph_enabled()
    }
    
    # Add graph statistics if available
    if is_graph_enabled():
        neo4j = get_neo4j()
        if neo4j:
            try:
                graph_stats = neo4j.get_graph_statistics()
                status_data["graph_statistics"] = graph_stats
            except Exception as e:
                status_data["graph_error"] = str(e)
    
    return status_data


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...), title: str = Form(None)):
    """
    Upload and process PDF with graph-enhanced ingestion.
    Builds both vector index (FAISS) and knowledge graph (Neo4j).
    """
    try:
        print(f"📤 Received upload request for file: {file.filename}")
        contents = await file.read()
        print(f"📄 File size: {len(contents)} bytes")
        
        # Use graph-enhanced ingestor if available
        ingestor = get_graph_ingestor()
        
        if ingestor and ingestor.build_graph:
            print(f"🔬 Using graph-enhanced ingestion (vector + knowledge graph)")
            metadata = {"title": title or file.filename}
            stats = ingestor.ingest_pdf(contents, file.filename, metadata)
            
            if not stats['success']:
                raise HTTPException(status_code=500, detail=stats.get('error', 'Unknown error'))
            
            print(f"✅ Graph-enhanced ingestion complete:")
            print(f"   📊 Chunks: {stats['chunks_created']}")
            print(f"   🧬 Entities: {stats['entities_extracted']}")
            print(f"   🔗 Graph nodes: {stats['graph_nodes_created']}")
            print(f"   🔗 Graph relationships: {stats['graph_relationships_created']}")
            
            return {
                "ingested_chunks": stats['chunks_created'],
                "entities_extracted": stats['entities_extracted'],
                "graph_nodes_created": stats['graph_nodes_created'],
                "graph_relationships_created": stats['graph_relationships_created'],
                "total_vectors_in_index": get_faiss().index.ntotal,
                "graph_enabled": True,
                "message": f"Successfully indexed {stats['chunks_created']} chunks and built knowledge graph from {file.filename}"
            }
        else:
            # Fallback to vector-only ingestion
            print(f"⚠️  Graph features unavailable - using vector-only ingestion")
            print(f"🔍 Extracting text from PDF...")
            text = extract_text_from_pdf_bytes(contents)
            if not text:
                raise HTTPException(status_code=400, detail="No text extracted from PDF")
            print(f"📝 Extracted text length: {len(text)} characters")
            
            print(f"✂️ Chunking text...")
            chunks = simple_chunk_text(text, approx_tokens=CHUNK_TOKEN_TARGET)
            if not chunks:
                raise HTTPException(status_code=400, detail="No chunks created from PDF")
            print(f"✂️ Created {len(chunks)} chunks")
            
            print(f"🧠 Initializing embedder...")
            embedder = get_embedder()
            print(f"🧠 Generating embeddings (this may take 1-2 minutes on first run)...")
            embeddings = embedder.embed_texts(chunks)
            
            if not embeddings or len(embeddings) == 0:
                raise HTTPException(status_code=500, detail="Failed to generate embeddings")
            print(f"✨ Generated {len(embeddings)} embeddings")
            
            print(f"💾 Adding to FAISS index...")
            faiss = get_faiss()
            print(f"📊 FAISS index before adding: {faiss.index.ntotal} vectors")
            metadatas = [{"source": file.filename, "title": title or file.filename, "text": chunk} for chunk in chunks]
            faiss.add(embeddings, metadatas)
            
            # Verify the vectors were added
            total_vectors = faiss.index.ntotal
            print(f"✅ FAISS index after adding: {total_vectors} vectors")
            print(f"💾 Index saved to: {faiss.index_path}")
            
            return {
                "ingested_chunks": len(chunks),
                "total_vectors_in_index": total_vectors,
                "graph_enabled": False,
                "message": f"Successfully indexed {len(chunks)} chunks from {file.filename} (vector-only mode)"
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR during upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {type(e).__name__}: {str(e)}")


@app.post("/chat")
async def chat(query: str = Form(...), level: str = Form("Novice"), use_graph: bool = Form(True)):
    """
    Chat endpoint with optional graph-enhanced retrieval.
    
    Args:
        query: User question
        level: Difficulty level (Novice/Intermediate/Advanced)
        use_graph: Whether to use graph-enhanced retrieval (if available)
    """
    faiss = get_faiss()
    embedder = get_embedder()
    
    # Check if index has any vectors
    if faiss.index.ntotal == 0:
        return {
            "answer": "⚠️ No documents have been uploaded yet. Please upload a PDF document first to enable the chat feature.",
            "contexts": [],
            "graph_used": False
        }
    
    contexts = []
    graph_used = False
    
    # Try graph-enhanced retrieval if enabled and requested
    if use_graph and is_graph_enabled():
        try:
            graph_retriever = get_graph_retriever()
            if graph_retriever:
                contexts = graph_retriever.retrieve(query, top_k=5, use_graph=True, expand_entities=True)
                graph_used = True
                print(f"✅ Used graph-enhanced retrieval")
        except Exception as e:
            print(f"⚠️  Graph retrieval failed, falling back to vector-only: {e}")
            graph_used = False
    
    # Fall back to standard vector retrieval if graph not used
    if not graph_used:
        q_emb = embedder.embed_texts([query])[0]
        contexts = faiss.query(q_emb, top_k=5)
    
    # Filter out invalid contexts (those with -inf scores)
    valid_contexts = [c for c in contexts if c.get('score', 0) > -1e30]
    
    if not valid_contexts:
        return {
            "answer": "⚠️ Could not find relevant information. Please try uploading more documents or rephrasing your question.",
            "contexts": [],
            "graph_used": graph_used
        }
    
    gen = get_generator()
    answer = gen.generate_answer(query, valid_contexts, level=level)
    return {
        "answer": answer, 
        "contexts": valid_contexts,
        "graph_used": graph_used
    }


@app.post("/quiz/start")
async def quiz_start(query: str = Form(...), level: str = Form("Novice")):
    faiss = get_faiss()
    quiz_gen = get_quiz()
    
    # If documents are available, use them for context
    if faiss.index.ntotal > 0:
        embedder = get_embedder()
        q_emb = embedder.embed_texts([query])[0]
        contexts = faiss.query(q_emb, top_k=5)
    else:
        # Generate quiz without context using general medical knowledge
        contexts = [{"metadata": {"text": f"Topic: {query}"}}]
    
    quiz = quiz_gen.generate(contexts, level=level, topic=query)
    return {"quiz": quiz}


@app.get("/citations")
async def citations():
    faiss = get_faiss()
    # return all known sources (dedupe)
    sources = {}
    for meta in faiss.id_to_meta.values():
        src = meta.get("source")
        if src:
            sources[src] = meta.get("title")
    return {"sources": sources}


# ============ Graph-Enhanced Endpoints ============

@app.get("/graph/status")
async def graph_status():
    """Check if graph features are enabled and get statistics"""
    if not is_graph_enabled():
        return {
            "enabled": False,
            "message": "Graph features not available. Check Neo4j connection."
        }
    
    neo4j = get_neo4j()
    stats = neo4j.get_graph_statistics()
    
    return {
        "enabled": True,
        "statistics": stats
    }


@app.get("/graph/procedure/{procedure_name}")
async def get_procedure_info(procedure_name: str):
    """Get comprehensive information about a surgical procedure from the knowledge graph"""
    if not is_graph_enabled():
        raise HTTPException(status_code=503, detail="Graph features not available")
    
    neo4j = get_neo4j()
    context = neo4j.get_procedure_context(procedure_name)
    
    if not context:
        raise HTTPException(status_code=404, detail=f"Procedure '{procedure_name}' not found in knowledge graph")
    
    return context


@app.get("/graph/related/{procedure_name}")
async def get_related_procedures(procedure_name: str, max_depth: int = 2):
    """Find procedures related to the given procedure"""
    if not is_graph_enabled():
        raise HTTPException(status_code=503, detail="Graph features not available")
    
    neo4j = get_neo4j()
    related = neo4j.find_related_procedures(procedure_name, max_depth=max_depth)
    
    return {
        "procedure": procedure_name,
        "related_procedures": related
    }


@app.post("/graph/extract_entities")
async def extract_entities(text: str = Form(...)):
    """Extract medical entities from text"""
    extractor = get_entity_extractor()
    
    if not extractor:
        raise HTTPException(status_code=503, detail="Entity extraction not available")
    
    entities = extractor.extract_entities(text)
    main_procedures = extractor.identify_main_procedures(text, top_n=5)
    
    return {
        "entities": entities,
        "main_procedures": [{"name": p[0], "frequency": p[1]} for p in main_procedures]
    }


@app.get("/graph/visualize")
async def visualize_graph():
    """Get graph data for visualization"""
    if not is_graph_enabled():
        raise HTTPException(status_code=503, detail="Graph features not available")
    
    neo4j = get_neo4j()
    
    # Get all procedures and their relationships
    with neo4j.driver.session() as session:
        # Get nodes
        nodes_result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, n.name as name, id(n) as id
            LIMIT 100
        """)
        
        nodes = [
            {
                "id": record["id"],
                "label": record["name"],
                "type": record["label"]
            }
            for record in nodes_result
        ]
        
        # Get relationships
        rels_result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN id(a) as source, id(b) as target, type(r) as type
            LIMIT 200
        """)
        
        edges = [
            {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"]
            }
            for record in rels_result
        ]
    
    return {
        "nodes": nodes,
        "edges": edges
    }


# ==================== MULTIMODAL ENDPOINTS ====================

def get_biomedclip():
    """Get BiomedCLIP embedder"""
    global _biomedclip, _multimodal_enabled
    
    if not MULTIMODAL_AVAILABLE:
        return None
    
    if _biomedclip is None:
        try:
            _biomedclip = BiomedCLIPEmbedder()
            print("✅ BiomedCLIP embedder loaded")
            _multimodal_enabled = True
        except Exception as e:
            print(f"⚠️  BiomedCLIP failed to load: {e}")
            _multimodal_enabled = False
    
    return _biomedclip


def get_image_processor():
    """Get surgical image processor"""
    global _image_processor
    
    if not MULTIMODAL_AVAILABLE:
        return None
    
    if _image_processor is None:
        _image_processor = SurgicalImageProcessor()
    
    return _image_processor


def get_multimodal_kg():
    """Get multimodal knowledge graph manager"""
    global _multimodal_kg
    
    if not MULTIMODAL_AVAILABLE or not GRAPH_IMPORTS_AVAILABLE:
        return None
    
    if _multimodal_kg is None:
        try:
            _multimodal_kg = MultimodalKGManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            print("✅ Multimodal knowledge graph initialized")
        except Exception as e:
            print(f"⚠️  Multimodal KG failed: {e}")
    
    return _multimodal_kg


def get_multimodal_retriever():
    """Get multimodal retriever"""
    global _multimodal_retriever
    
    if _multimodal_retriever is None:
        text_embedder = get_embedder()
        visual_embedder = get_biomedclip()
        faiss = get_faiss()
        kg = get_multimodal_kg()
        extractor = get_entity_extractor()
        
        if visual_embedder and kg and extractor:
            _multimodal_retriever = MultimodalRetriever(
                text_embedder, visual_embedder, faiss, kg, extractor
            )
            print("✅ Multimodal retriever initialized")
    
    return _multimodal_retriever


def get_image_storage():
    """Get image storage manager"""
    global _image_storage
    
    if not MULTIMODAL_AVAILABLE:
        return None
    
    if _image_storage is None:
        from app.config import IMAGE_STORAGE_PATH
        _image_storage = ImageStorageManager(IMAGE_STORAGE_PATH)
        print(f"✅ Image storage initialized at {IMAGE_STORAGE_PATH}")
    
    return _image_storage


def is_multimodal_enabled():
    """Check if multimodal features are available"""
    get_biomedclip()
    return _multimodal_enabled


@app.post("/upload_image")
async def upload_image(
    file: UploadFile = File(...),
    procedure: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload surgical image and add to multimodal knowledge graph.
    Supports MICCAI research: automated image annotation and graph construction.
    """
    if not is_multimodal_enabled():
        raise HTTPException(
            status_code=503, 
            detail="Multimodal features not available. Please install: pip install open-clip-torch pillow opencv-python"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, etc.)")
    
    try:
        # Read image
        contents = await file.read()
        
        # Validate image can be opened
        try:
            image = Image.open(BytesIO(contents)).convert('RGB')
        except Exception as img_err:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid image file: {str(img_err)}"
            )
        
        # Process image
        processor = get_image_processor()
        if not processor:
            raise HTTPException(status_code=503, detail="Image processor not available")
        
        quality = processor.assess_image_quality(image)
        
        # Generate image embedding
        biomedclip = get_biomedclip()
        if not biomedclip:
            raise HTTPException(status_code=503, detail="BiomedCLIP not available")
        
        try:
            embedding = biomedclip.embed_images([image])[0]
        except Exception as embed_err:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate embeddings: {str(embed_err)}"
            )
        
        # Detect instruments and phases
        try:
            instruments = biomedclip.find_surgical_instruments(image)
            phases = biomedclip.identify_surgical_phase(image)
        except Exception as detect_err:
            # Continue even if detection fails
            instruments = {'predictions': [], 'probabilities': []}
            phases = {'top_prediction': 'unknown', 'confidence': 0.0}
            print(f"⚠️ Detection failed: {detect_err}")
        
        # Generate unique image ID
        import uuid
        image_id = f"img_{uuid.uuid4().hex[:12]}"
        
        # Save to storage
        storage = get_image_storage()
        if storage:
            try:
                storage.save_image(
                    image_bytes=contents,
                    filename=file.filename,
                    procedure=procedure,
                    quality_score=quality.get('quality_score', 0),
                    detected_instruments=instruments.get('predictions', [])[:5],
                    surgical_phase=phases.get('top_prediction'),
                    additional_metadata={
                        'description': description,
                        'width': image.width,
                        'height': image.height
                    }
                )
            except Exception as storage_err:
                print(f"⚠️ Storage failed: {storage_err}")
        
        # Save to knowledge graph
        kg = get_multimodal_kg()
        if kg:
            try:
                # Create image node
                kg.create_image_node(
                    image_id=image_id,
                    image_path=file.filename,
                    embedding=embedding.tolist(),
                    metadata={
                        'width': image.width,
                        'height': image.height,
                        'quality_score': quality.get('quality_score', 0)
                    }
                )
                
                # Link to procedure if provided
                if procedure:
                    kg.link_image_to_procedure(image_id, procedure, confidence=1.0)
                
                # Link detected instruments
                for inst in instruments.get('predictions', [])[:3]:
                    if inst['probability'] > 0.2:
                        kg.link_image_to_instrument(
                            image_id, inst['category'], inst['probability']
                        )
                
                # Link to surgical phase
                if phases.get('confidence', 0) > 0.3:
                    phase_name = phases['top_prediction']
                    # Create phase node if doesn't exist
                    kg.create_surgical_phase_node(phase_name)
            except Exception as kg_err:
                print(f"⚠️ Knowledge graph update failed: {kg_err}")
        
        return {
            "status": "success",
            "image_id": image_id,
            "quality": quality,
            "detected_instruments": instruments.get('predictions', [])[:5],
            "detected_phase": {
                "phase": phases.get('top_prediction', 'unknown'),
                "confidence": phases.get('confidence', 0.0)
            },
            "message": f"Image uploaded and analyzed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in upload_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/visual_qa")
async def visual_qa(
    file: UploadFile = File(...),
    question: str = Form(...)
):
    """
    Visual Question Answering for surgical images.
    MICCAI innovation: Zero-shot surgical image understanding.
    """
    if not is_multimodal_enabled():
        raise HTTPException(
            status_code=503,
            detail="Multimodal features not available. Please install: pip install open-clip-torch pillow opencv-python"
        )
    
    # Validate inputs
    if not question or len(question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, etc.)")
    
    try:
        # Read image
        contents = await file.read()
        
        try:
            image = Image.open(BytesIO(contents)).convert('RGB')
        except Exception as img_err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(img_err)}"
            )
        
        # Get multimodal retriever
        retriever = get_multimodal_retriever()
        
        if retriever:
            # Use multimodal retriever for VQA
            try:
                result = retriever.visual_qa(image, question, use_graph=True)
            except Exception as vqa_err:
                print(f"⚠️ VQA failed, using fallback: {vqa_err}")
                retriever = None  # Fall back to basic method
        
        if not retriever:
            # Fallback to basic CLIP
            biomedclip = get_biomedclip()
            
            if not biomedclip:
                raise HTTPException(status_code=503, detail="BiomedCLIP not available")
            
            # Basic analysis based on question type
            try:
                if 'instrument' in question.lower():
                    instruments = biomedclip.find_surgical_instruments(image)
                    detected = [p['category'] for p in instruments.get('predictions', [])[:3]]
                    answer = f"Detected instruments: {', '.join(detected) if detected else 'None detected'}"
                    confidence = instruments.get('confidence', 0.0)
                elif 'phase' in question.lower():
                    phases = biomedclip.identify_surgical_phase(image)
                    answer = f"Surgical phase: {phases.get('top_prediction', 'unknown')}"
                    confidence = phases.get('confidence', 0.0)
                else:
                    answer = "I can answer questions about surgical instruments and phases in images."
                    confidence = 0.0
                
                result = {
                    'question': question,
                    'answer': answer,
                    'confidence': confidence,
                    'method': 'biomedclip_only'
                }
            except Exception as analysis_err:
                raise HTTPException(
                    status_code=500,
                    detail=f"Image analysis failed: {str(analysis_err)}"
                )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in visual_qa: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/multimodal_search")
async def multimodal_search(
    text_query: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    top_k: int = Form(5),
    return_images: bool = Form(True),
    return_text: bool = Form(True)
):
    """
    Multimodal retrieval supporting text, image, or both.
    MICCAI innovation: Cross-modal surgical knowledge retrieval.
    """
    if not is_multimodal_enabled():
        # Fallback to text-only search
        if text_query:
            retriever = get_graph_retriever() or get_faiss()
            if hasattr(retriever, 'retrieve'):
                results = retriever.retrieve(text_query, top_k=top_k)
            else:
                embedder = get_embedder()
                query_emb = embedder.embed_texts([text_query])[0]
                results = retriever.query(query_emb, top_k=top_k)
            
            return {"results": results, "mode": "text_only"}
        else:
            raise HTTPException(status_code=503, detail="Multimodal features not available")
    
    try:
        image_query = None
        if file:
            contents = await file.read()
            image_query = Image.open(BytesIO(contents)).convert('RGB')
        
        retriever = get_multimodal_retriever()
        
        if retriever:
            results = retriever.retrieve_multimodal(
                text_query=text_query,
                image_query=image_query,
                top_k=top_k,
                return_images=return_images,
                return_text=return_text
            )
        else:
            raise HTTPException(status_code=503, detail="Multimodal retriever not initialized")
        
        return {
            "results": results,
            "mode": "multimodal",
            "query_types": {
                "text": text_query is not None,
                "image": image_query is not None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/multimodal/status")
async def multimodal_status():
    """Get multimodal system status"""
    status = {
        "multimodal_available": MULTIMODAL_AVAILABLE,
        "multimodal_enabled": is_multimodal_enabled(),
        "graph_enabled": is_graph_enabled(),
        "capabilities": []
    }
    
    if is_multimodal_enabled():
        status["capabilities"].extend([
            "visual_qa",
            "image_upload",
            "cross_modal_search",
            "image_storage"
        ])
        
        retriever = get_multimodal_retriever()
        if retriever:
            stats = retriever.get_statistics()
            status["statistics"] = stats
        
        # Add storage statistics
        storage = get_image_storage()
        if storage:
            storage_stats = storage.get_statistics()
            status["storage"] = storage_stats
    
    return status


@app.get("/images/statistics")
async def get_image_statistics():
    """Get image storage statistics"""
    storage = get_image_storage()
    if not storage:
        raise HTTPException(status_code=503, detail="Image storage not available")
    
    try:
        stats = storage.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/list")
async def list_images(
    procedure: Optional[str] = None,
    min_quality: Optional[float] = None,
    phase: Optional[str] = None,
    limit: int = 100
):
    """List stored images with optional filters"""
    storage = get_image_storage()
    if not storage:
        raise HTTPException(status_code=503, detail="Image storage not available")
    
    try:
        images = storage.list_images(
            procedure=procedure,
            min_quality=min_quality,
            phase=phase,
            limit=limit
        )
        return {"images": images, "count": len(images)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{image_id}")
async def get_image_metadata(image_id: str):
    """Get metadata for a specific image"""
    storage = get_image_storage()
    if not storage:
        raise HTTPException(status_code=503, detail="Image storage not available")
    
    try:
        metadata = storage.get_image(image_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Image not found")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
