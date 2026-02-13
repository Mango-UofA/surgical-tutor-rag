"""
Start the FastAPI backend server with optimized reload settings
"""

import uvicorn
import os

if __name__ == "__main__":
    # Get the directory of this script
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Directories and patterns to exclude from auto-reload
    reload_excludes = [
        "start_server.py",  # Exclude this file itself
        "evaluation/*",
        "test_*.py",
        "*_test.py",
        "*.md",
        "*.txt",
        "*.json",
        "__pycache__/*",
        "*.pyc",
        ".git/*",
        "faiss_index.*",
        "uploaded_images/*",
        "modules/**/*.pyc",
        "app/**/*.pyc"
    ]
    
    print("🚀 Starting Surgical Tutor RAG Backend")
    print("📍 Backend directory:", backend_dir)
    print("🔄 Auto-reload enabled (excluding test/evaluation files)")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=reload_excludes,
        reload_dirs=["app", "modules"],  # Only watch app and modules directories
        log_level="info"
    )
