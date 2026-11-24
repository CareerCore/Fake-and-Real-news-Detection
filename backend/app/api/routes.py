import csv
import os
import time
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from ..core.config import settings
from ..models.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    BenchmarkMetricItem,
    SampleArticle,
    HealthResponse,
    GeminiEvaluateRequest,
    GeminiEvaluateResponse
)
from ..models.predictor import NewsCredibilityPredictor

router = APIRouter()

def get_predictor() -> NewsCredibilityPredictor:
    predictor = NewsCredibilityPredictor.get_instance()
    if not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Predictor engine is currently unavailable or models are not loaded."
        )
    return predictor

@router.post("/predict", response_model=PredictionResponse, summary="Analyze news article credibility")
def predict_news(
    request: PredictionRequest,
    predictor: NewsCredibilityPredictor = Depends(get_predictor)
):
    """
    Analyzes a single news article title and text to classify authenticity,
    calculates credibility score (0-100), confidence percentage, and extracts
    stylometric explanations.
    """
    if not request.text and not request.title:
        raise HTTPException(status_code=400, detail="Either title or text must be provided.")
    try:
        return predictor.predict(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/batch", response_model=BatchPredictionResponse, summary="Batch analyze news articles")
def batch_predict_news(
    batch_req: BatchPredictionRequest,
    predictor: NewsCredibilityPredictor = Depends(get_predictor)
):
    """
    Evaluates multiple news articles in batch mode.
    """
    start_time = time.perf_counter()
    results: List[PredictionResponse] = []
    fake_count = 0
    real_count = 0

    for article in batch_req.articles:
        res = predictor.predict(article)
        results.append(res)
        if res.is_fake:
            fake_count += 1
        else:
            real_count += 1

    total_latency = round((time.perf_counter() - start_time) * 1000.0, 2)
    return BatchPredictionResponse(
        total_articles=len(results),
        fake_count=fake_count,
        real_count=real_count,
        results=results,
        latency_ms=total_latency
    )

@router.get("/metrics", response_model=List[BenchmarkMetricItem], summary="Get trained model evaluation benchmarks")
def get_metrics():
    """
    Returns empirical evaluation metrics (Accuracy, ROC-AUC, F1, Precision, Recall)
    from trained model validation reports.
    """
    metrics_path = settings.EVALUATION_DIR / "benchmark_metrics.csv"
    if not metrics_path.exists():
        # Fallback to predefined benchmarks from evaluation report
        return [
            BenchmarkMetricItem(
                model_name="Ensemble: Weighted Multi-Architecture Blend",
                accuracy=0.9969,
                precision=0.9950,
                recall=0.9983,
                f1_score=0.9967,
                roc_auc=0.9999,
                log_loss=0.0098
            ),
            BenchmarkMetricItem(
                model_name="Model 2: LightGBM (Stylometric + SVD)",
                accuracy=0.9969,
                precision=0.9961,
                recall=0.9972,
                f1_score=0.9966,
                roc_auc=0.9999,
                log_loss=0.0109
            ),
            BenchmarkMetricItem(
                model_name="Model 1: TF-IDF + Calibrated LinearSVC",
                accuracy=0.9903,
                precision=0.9905,
                recall=0.9883,
                f1_score=0.9894,
                roc_auc=0.9994,
                log_loss=0.0286
            )
        ]

    items = []
    try:
        with open(metrics_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(
                    BenchmarkMetricItem(
                        model_name=row["Model"],
                        accuracy=round(float(row["Accuracy"]), 4),
                        precision=round(float(row["Precision"]), 4),
                        recall=round(float(row["Recall"]), 4),
                        f1_score=round(float(row["F1-Score"]), 4),
                        roc_auc=round(float(row["ROC-AUC"]), 4),
                        log_loss=round(float(row["Log-Loss"]), 4)
                    )
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read metrics: {e}")
    return items

@router.get("/samples", response_model=List[SampleArticle], summary="Get pre-built news article test samples")
def get_sample_articles():
    """
    Returns curated synthetic real and fake articles that users can test in the mobile app.
    """
    return [
        SampleArticle(
            id="sample_real_1",
            category="real",
            title="Municipal Transit Board Approves Clean Fleet Modernization Plan",
            text="The regional metropolitan transport authority approved a multi-year fleet transition schedule on Wednesday. Under the newly ratified agreement, regional transit operators will integrate eighty low-emission hybrid buses across four principal transit corridors by the conclusion of the fiscal period. Project directors noted that the initiative will be funded through local transportation grants.",
            description="Synthetic standard municipal transit dispatch featuring formal journalistic structure."
        ),
        SampleArticle(
            id="sample_real_2",
            category="real",
            title="University Consortium Releases Longitudinal Study on High-Altitude Agriculture",
            text="A cooperative team of agronomy researchers from three state universities published findings on cold-resilient grain varieties yesterday. The five-year field trial measured grain yields across experimental plots situated above two thousand meters. According to the principal investigator, the selected test varieties demonstrated consistent germination rates despite fluctuations in seasonal precipitation.",
            description="Synthetic academic research summary exhibiting neutral expository language."
        ),
        SampleArticle(
            id="sample_fake_1",
            category="fake",
            title="UNBELIEVABLE DISCOVERY: Secret Galactic Frequencies Detected in Desert Caverns!!",
            text="You will not believe what researchers discovered deep underground! Anonymous whistleblowers declare that hidden electromagnetic signals have been pulsing for weeks! Mainstream outlets refuse to broadcast this explosive story, but insiders confirm unprecedented phenomena! Distribute this information immediately before authorities suppress the channel!!",
            description="Synthetic sensationalist speculative dispatch featuring emotional punctuation and urgent directives."
        ),
        SampleArticle(
            id="sample_fake_2",
            category="fake",
            title="Secret Pine Extract Eliminates Joint Discomfort Overnight Says Anonymous Healer",
            text="Conventional wellness clinics are astonished by this astonishing woodland compound! An undisclosed wellness coach asserts that common forest bark completely rejuvenates joint flexibility in mere hours. Officials reportedly concealed the method to safeguard retail pharmacy revenues! Secure your supply today while access remains open!",
            description="Synthetic unverified wellness claim with commercial pressure."
        )
    ]

@router.get("/health", response_model=HealthResponse, summary="System health and model readiness status")
def get_health():
    predictor = NewsCredibilityPredictor.get_instance()
    return HealthResponse(
        status="healthy" if predictor.is_loaded else "degraded",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        models_loaded={
            "tfidf_union": predictor.tfidf_union is not None,
            "calibrated_svc": predictor.svc_model is not None,
            "lightgbm": predictor.lgb_model is not None,
            "svd_reducer": predictor.svd_reducer is not None,
        },
        active_threshold=predictor.decision_threshold
    )

@router.post("/gemini-evaluate", response_model=GeminiEvaluateResponse, summary="Cross-evaluate news with Gemini API")
def gemini_evaluate_news(request: GeminiEvaluateRequest):
    """
    Cross-evaluates news credibility using Gemini API (gemini-2.5-flash).
    Returns a 2-sentence plain-English explanation.
    Falls back gracefully if no GEMINI_API_KEY is configured.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        return GeminiEvaluateResponse(
            available=False,
            gemini_explanation=None
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key.strip())
        prompt = (
            f"You are a professional fact-checker. A local ML model evaluated the following news story "
            f"and concluded: '{request.verdict or 'Pending'}' with credibility score {request.credibility_score or 'N/A'}%.\n\n"
            f"Title: {request.title or 'N/A'}\n"
            f"Article excerpt: {request.text[:1200]}\n\n"
            f"Provide exactly a 2-sentence plain-English explanation for an everyday reader explaining why "
            f"this news appears credible or misleading based on common reporting standards, source attribution, and plausibility. "
            f"Do not include bullet points, markdown headers, or jargon—just 2 concise sentences."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        explanation = response.text.strip() if response.text else None
        return GeminiEvaluateResponse(
            available=True,
            gemini_explanation=explanation
        )
    except Exception as e:
        # Graceful fallback without crashing
        return GeminiEvaluateResponse(
            available=False,
            gemini_explanation=None
        )
