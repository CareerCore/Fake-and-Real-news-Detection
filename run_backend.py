"""
Root convenience script to start the CrediNews AI Web Application and FastAPI Backend.
Usage:
    python run_backend.py
"""
import uvicorn
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    print("==================================================================")
    print("🚀 Starting CrediNews AI Detection Platform...")
    print("📍 Interactive Web Application: http://127.0.0.1:8000")
    print("📍 API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print("📍 OpenAPI JSON Specification:  http://127.0.0.1:8000/openapi.json")
    print("==================================================================")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
