#!/bin/bash
# Start the Surgical Tutor RAG Backend
# Run this from the backend directory

echo "🚀 Starting Surgical Tutor RAG Backend"
echo "📍 Backend directory: $PWD"
echo "🔄 Auto-reload enabled (watching app/ and modules/ only)"
echo "🌐 Server: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run uvicorn with optimized reload settings
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir app \
  --reload-dir modules \
  --reload-exclude "evaluation/*" \
  --reload-exclude "test_*.py" \
  --reload-exclude "*.md" \
  --log-level info
