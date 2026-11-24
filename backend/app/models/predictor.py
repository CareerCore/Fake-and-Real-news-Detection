import json
import logging
import time
from typing import Optional
import joblib
import numpy as np

from ..core.config import settings
from .schemas import (
    PredictionRequest,
    PredictionResponse,
    StylometricFeatures,
    ModelScores
)
from .stylometrics import extract_stylometrics

logger = logging.getLogger("news_credibility_engine")

class NewsCredibilityPredictor:
    """
    Inference engine for Fake and Real News detection.
    Primary Classifier: Calibrated LinearSVC (TF-IDF word 1-3 n-grams + char 3-5 n-grams)
    Dataset Ground Truth: 0 = Real / Verified News, 1 = Fake / Unverified News
    """
    _instance: Optional["NewsCredibilityPredictor"] = None
    
    def __init__(self):
        self.tfidf_union = None
        self.svc_model = None
        self.lgb_model = None
        self.svd_reducer = None
        self.ensemble_weights = [1.0, 0.0, 0.0]
        self.decision_threshold = settings.DECISION_THRESHOLD
        self.is_loaded = False
        self._load_models()

    @classmethod
    def get_instance(cls) -> "NewsCredibilityPredictor":
        if cls._instance is None:
            cls._instance = NewsCredibilityPredictor()
        return cls._instance

    def _load_models(self):
        try:
            logger.info("Loading ensemble configuration...")
            if settings.CONFIG_PATH.exists():
                with open(settings.CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.ensemble_weights = cfg.get("weights", self.ensemble_weights)
                    self.decision_threshold = cfg.get("decision_threshold", self.decision_threshold)
            
            logger.info(f"Loading TF-IDF Union from {settings.TFIDF_PATH}...")
            if settings.TFIDF_PATH.exists():
                self.tfidf_union = joblib.load(settings.TFIDF_PATH)
            else:
                logger.warning(f"TF-IDF vectorizer not found at {settings.TFIDF_PATH}")

            logger.info(f"Loading Calibrated LinearSVC from {settings.SVC_PATH}...")
            if settings.SVC_PATH.exists():
                self.svc_model = joblib.load(settings.SVC_PATH)
            else:
                logger.warning(f"SVC model not found at {settings.SVC_PATH}")

            # Auxiliary LightGBM and SVD models (if present)
            if settings.LGB_PATH.exists():
                try:
                    self.lgb_model = joblib.load(settings.LGB_PATH)
                    logger.info("LightGBM model loaded.")
                except Exception as e:
                    logger.warning(f"Could not load LightGBM model: {e}")
            
            if settings.SVD_PATH.exists():
                try:
                    self.svd_reducer = joblib.load(settings.SVD_PATH)
                    logger.info("SVD Reducer loaded.")
                except Exception as e:
                    logger.warning(f"Could not load SVD Reducer: {e}")

            self.is_loaded = (self.tfidf_union is not None and self.svc_model is not None)
            logger.info(f"Predictor initialized. Primary models ready: {self.is_loaded}")
        except Exception as e:
            logger.error(f"Fatal error while loading model artifacts: {e}", exc_info=True)
            self.is_loaded = False

    def predict(self, req: PredictionRequest) -> PredictionResponse:
        start_time = time.perf_counter()
        
        if not self.is_loaded:
            raise RuntimeError("Model engine not loaded. Please ensure model_assets are present.")

        title = (req.title or "").strip()
        text = (req.text or "").strip()
        full_text = f"{title} {text}".strip()
        if not full_text:
            raise ValueError("Either title or text must be provided.")
        
        # 1. Stylometrics & Explainability Tags
        sty_features, raw_sty_vec, tags = extract_stylometrics(title, text)
        
        # 2. TF-IDF feature extraction
        tfidf_vec = self.tfidf_union.transform([full_text])
        
        # 3. Calibrated LinearSVC Prediction (Ground Truth: Class 0 = Real, Class 1 = Fake)
        svc_proba = self.svc_model.predict_proba(tfidf_vec)[0]
        svc_fake_prob = float(svc_proba[1])

        # 4. Optional LightGBM auxiliary calculation
        lgb_fake_prob = None
        has_lgb = (self.lgb_model is not None and self.svd_reducer is not None and self.ensemble_weights[1] > 0.0)
        if has_lgb:
            try:
                svd_vec = self.svd_reducer.transform(tfidf_vec)[0]
                lgb_features = np.hstack([raw_sty_vec, svd_vec]).reshape(1, -1)
                lgb_proba = self.lgb_model.predict_proba(lgb_features)[0]
                lgb_fake_prob = float(lgb_proba[1])
            except Exception as e:
                logger.warning(f"LightGBM prediction failed: {e}. Falling back to SVC.")
                lgb_fake_prob = None

        # 5. Prediction blending (SVC is primary calibrated authority)
        w_svc = self.ensemble_weights[0]
        w_lgb = self.ensemble_weights[1] if lgb_fake_prob is not None else 0.0
        total_w = w_svc + w_lgb
        if total_w > 0:
            final_fake_prob = (w_svc * svc_fake_prob + (w_lgb * (lgb_fake_prob or 0.0))) / total_w
        else:
            final_fake_prob = svc_fake_prob

        # Decision threshold comparison
        threshold = req.threshold if req.threshold is not None else self.decision_threshold
        is_fake = bool(final_fake_prob >= threshold)
        
        # Credibility Score: 0.0 to 100.0 (100 = Verified Real News, 0 = Fabricated News)
        raw_credibility = (1.0 - final_fake_prob) * 100.0
        credibility_score = round(float(np.clip(raw_credibility, 0.5, 99.5)), 1)
        
        fake_prob_rounded = round(float(np.clip(final_fake_prob, 0.001, 0.999)), 4)
        real_prob_rounded = round(1.0 - fake_prob_rounded, 4)
        
        # Human-Readable Verdict & Risk Assessment
        if is_fake:
            verdict = "Suspicious / Fake News"
            if final_fake_prob >= 0.80:
                confidence_level = "High"
                risk_assessment = "Critical Misinformation Risk: Content exhibits strong hallmarks of fabrication, sensationalism, or unverified claims."
            elif final_fake_prob >= 0.60:
                confidence_level = "Moderate"
                risk_assessment = "Moderate Misinformation Risk: Phrasing, emotional punctuation, or unverified claims detected."
            else:
                confidence_level = "Low"
                risk_assessment = "Low-to-Moderate Suspicion: Exceeds suspicion threshold; corroboration with verified primary sources advised."
        else:
            verdict = "Verified Real News"
            if final_fake_prob <= 0.20:
                confidence_level = "High"
                risk_assessment = "Minimal Risk: Strong linguistic and editorial alignment with verified journalistic reporting."
            elif final_fake_prob <= 0.40:
                confidence_level = "Moderate"
                risk_assessment = "Low Risk: Content generally reflects standard editorial reporting standards."
            else:
                confidence_level = "Borderline"
                risk_assessment = "Borderline Credible: Meets authenticity thresholds, but secondary fact-checking is advised."

        confidence_pct = round(max(real_prob_rounded, fake_prob_rounded) * 100.0, 1)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return PredictionResponse(
            verdict=verdict,
            is_fake=is_fake,
            credibility_score=credibility_score,
            fake_probability=fake_prob_rounded,
            real_probability=real_prob_rounded,
            confidence_level=confidence_level,
            confidence_score=confidence_pct,
            risk_assessment=risk_assessment,
            explanation_tags=tags,
            stylometrics=sty_features,
            model_scores=ModelScores(
                calibrated_svc_fake_prob=round(svc_fake_prob, 4),
                lightgbm_fake_prob=round(lgb_fake_prob, 4) if lgb_fake_prob is not None else None,
                ensemble_fake_prob=round(final_fake_prob, 4)
            ),
            latency_ms=elapsed_ms
        )
