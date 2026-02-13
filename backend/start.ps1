# Start the Surgical Tutor RAG Backend
# Run this from the backend directory

Write-Host "🚀 Starting Surgical Tutor RAG Backend" -ForegroundColor Green
Write-Host "📍 Backend directory: $PWD" -ForegroundColor Cyan
Write-Host "🔄 Auto-reload enabled (watching app/ and modules/ only)" -ForegroundColor Yellow
Write-Host "🌐 Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Run uvicorn with optimized reload settings
uvicorn app.main:app `
  --host 0.0.0.0 `
  --port 8000 `
  --reload `
  --reload-dir app `
  --reload-dir modules `
  --reload-exclude "evaluation/*" `
  --reload-exclude "test_*.py" `
  --reload-exclude "*.md" `
  --log-level info
