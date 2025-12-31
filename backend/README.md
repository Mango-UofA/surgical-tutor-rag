Surgical Tutor — Backend

This directory contains the FastAPI backend for the Surgical Tutor RAG system.

Key modules:
- data_ingestion: PDF parsing/cleaning/chunking
- embedder: BioClinicalBERT embeddings
- retriever: FAISS management (created later)
- generator: LangChain + OpenAI integration (created later)
- quiz_generator: quiz creation logic (created later)

Env vars:
- MONGODB_URI
- OPENAI_API_KEY
- FAISS_INDEX_PATH (optional)

To install dependencies:

python -m pip install -r requirements.txt

Run development server:

uvicorn app.main:app --reload --port 8000
