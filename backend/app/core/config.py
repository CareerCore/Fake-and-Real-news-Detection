import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "CrediNews AI - Fake & Real News Detection Platform"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "2.2.0"
    DESCRIPTION: str = (
        "Enterprise-grade Fake News & Media Credibility Detection Engine. "
        "Powered by Calibrated LinearSVC (Word + Char n-grams), LightGBM, and Stylometric NLP."
    )
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    MODEL_DIR: Path = BASE_DIR / "model_assets"
    EVALUATION_DIR: Path = BASE_DIR / "evaluation_reports"
    STATIC_DIR: Path = BASE_DIR / "backend" / "static"
    
    # Load .env if present
    env_file: Path = BASE_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line and not _line.startswith("#") and "=" in _line:
                        _k, _v = _line.split("=", 1)
                        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
        except Exception:
            pass

    # Model Artifact Paths
    TFIDF_PATH: Path = MODEL_DIR / "tfidf_union.joblib"
    SVC_PATH: Path = MODEL_DIR / "model_1_svc.joblib"
    LGB_PATH: Path = MODEL_DIR / "model_2_lgb.joblib"
    SVD_PATH: Path = MODEL_DIR / "svd_reducer.joblib"
    CONFIG_PATH: Path = MODEL_DIR / "ensemble_config.json"
    
    # Standard classification threshold (prob >= 0.50 classified as Fake/Suspicious)
    DECISION_THRESHOLD: float = 0.50
    
    # Gemini API (optional — set GEMINI_API_KEY env var to enable)
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    
    # Server host and port
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "*",
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000"
    ]

settings = Settings()
