import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .api.routes import router
from .models.predictor import NewsCredibilityPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("news_credibility_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload models into memory
    logger.info("Initializing ML Prediction Engine...")
    predictor = NewsCredibilityPredictor.get_instance()
    if predictor.is_loaded:
        logger.info("ML Prediction Engine successfully initialized and warm.")
    else:
        logger.warning("ML Prediction Engine initialized in degraded mode. Check model paths.")
    yield
    # Shutdown
    logger.info("Shutting down Fake News Detection Service.")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (Web App Assets)
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API router
app.include_router(router, prefix=settings.API_V1_STR, tags=["Credibility AI"])

@app.get("/", include_in_schema=False)
def root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")

@app.get("/api/v1", tags=["Meta"])
def api_meta():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "web_ui": "/",
            "predict": f"{settings.API_V1_STR}/predict",
            "batch": f"{settings.API_V1_STR}/predict/batch",
            "metrics": f"{settings.API_V1_STR}/metrics",
            "samples": f"{settings.API_V1_STR}/samples",
            "health": f"{settings.API_V1_STR}/health",
            "documentation": "/docs"
        }
    }
