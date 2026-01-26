import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

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

# Graph-enhanced modules
from modules.graph.neo4j_manager import Neo4jManager
from modules.graph.entity_extractor import MedicalEntityExtractor
from modules.graph.graph_retriever import GraphEnhancedRetriever
from modules.graph.graph_ingestor import GraphEnhancedIngestor

app = FastAPI(title="Surgical Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize embedder and faiss manager lazily
_embedder: BioClinicalEmbedder | None = None
_faiss: FaissManager | None = None
_gen: Generator | None = None
_quiz: QuizGenerator | None = None

# Graph-enhanced components
_neo4j: Neo4jManager | None = None
_entity_extractor: MedicalEntityExtractor | None = None
_graph_retriever: GraphEnhancedRetriever | None = None
_graph_ingestor: GraphEnhancedIngestor | None = None
_graph_enabled: bool = False


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
        
        if neo4j and extractor:
            _graph_retriever = GraphEnhancedRetriever(
                faiss, neo4j, extractor,
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
    try:
        print(f"📤 Received upload request for file: {file.filename}")
        contents = await file.read()
        print(f"📄 File size: {len(contents)} bytes")
        
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
            "message": f"Successfully indexed {len(chunks)} chunks from {file.filename}"
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
    
    # Check if index has any vectors
    if faiss.index.ntotal == 0:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a PDF document first.")
    
    embedder = get_embedder()
    q_emb = embedder.embed_texts([query])[0]
    contexts = faiss.query(q_emb, top_k=5)
    quiz_gen = get_quiz()
    quiz = quiz_gen.generate(contexts, level=level)
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

