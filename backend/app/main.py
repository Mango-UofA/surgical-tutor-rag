import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.config import BIOCLINICALBERT_MODEL, CHUNK_TOKEN_TARGET, FAISS_INDEX_PATH
from app.db import get_db
from modules.data_ingestion.pdf_parser import extract_text_from_pdf_bytes
from modules.data_ingestion.chunker import simple_chunk_text
from modules.embedder.embedder import BioClinicalEmbedder
from modules.retriever.faiss_manager import FaissManager
from modules.generator.generator import Generator
from modules.quiz_generator.quiz_generator import QuizGenerator

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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    """Check system status and index statistics"""
    faiss = get_faiss()
    return {
        "status": "ok",
        "vectors_in_index": faiss.index.ntotal,
        "documents_indexed": len(set(meta.get("source") for meta in faiss.id_to_meta.values())),
        "total_chunks": len(faiss.id_to_meta)
    }


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
async def chat(query: str = Form(...), level: str = Form("Novice")):
    faiss = get_faiss()
    embedder = get_embedder()
    
    # Check if index has any vectors
    if faiss.index.ntotal == 0:
        return {
            "answer": "⚠️ No documents have been uploaded yet. Please upload a PDF document first to enable the chat feature.",
            "contexts": []
        }
    
    q_emb = embedder.embed_texts([query])[0]
    contexts = faiss.query(q_emb, top_k=5)
    
    # Filter out invalid contexts (those with -inf scores)
    valid_contexts = [c for c in contexts if c['score'] > -1e30]
    
    if not valid_contexts:
        return {
            "answer": "⚠️ Could not find relevant information. Please try uploading more documents or rephrasing your question.",
            "contexts": []
        }
    
    gen = get_generator()
    answer = gen.generate_answer(query, valid_contexts, level=level)
    return {"answer": answer, "contexts": valid_contexts}


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
