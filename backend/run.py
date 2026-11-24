import uvicorn
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    print("==================================================")
    print("   Starting Fake News Credibility Detection API   ")
    print("   Docs: http://127.0.0.1:8000/docs               ")
    print("==================================================")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
