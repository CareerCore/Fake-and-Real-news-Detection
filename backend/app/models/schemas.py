from typing import Optional, List
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    title: Optional[str] = Field(
        default="",
        description="The headline or title of the news article.",
        json_schema_extra={"example": "Breaking: Scientific consensus reaches new milestone on clean energy efficiency"}
    )
    text: str = Field(
        ...,
        description="The full body text of the news article to be analyzed.",
        json_schema_extra={"example": "A major international research coalition announced findings today showing solar conversion rates have doubled under new perovskite crystal configurations."}
    )
    threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional custom classification threshold (default is 0.25)."
    )

class BatchPredictionRequest(BaseModel):
    articles: List[PredictionRequest] = Field(
        ...,
        description="List of articles to evaluate in batch mode."
    )

class StylometricFeatures(BaseModel):
    title_word_count: int
    title_char_length: int
    text_word_count: int
    text_char_length: int
    avg_word_length: float
    uppercase_ratio: float
    punctuation_ratio: float
    exclamation_count: int
    question_count: int
    quote_count: int
    lexical_diversity: float

class ModelScores(BaseModel):
    calibrated_svc_fake_prob: float
    lightgbm_fake_prob: Optional[float] = None
    ensemble_fake_prob: float

class PredictionResponse(BaseModel):
    verdict: str = Field(..., description="'Verified Real News' or 'Suspicious / Fake News'")
    is_fake: bool = Field(..., description="True if predicted as fake/unverified news.")
    credibility_score: float = Field(..., description="0 to 100 credibility score (100 = verified real, 0 = extreme fake).")
    fake_probability: float = Field(..., description="Estimated probability of article being fake (0.0 to 1.0).")
    real_probability: float = Field(..., description="Estimated probability of article being real (0.0 to 1.0).")
    confidence_level: str = Field(..., description="'High', 'Moderate', or 'Low'")
    confidence_score: float = Field(..., description="Confidence percentage of the primary prediction.")
    risk_assessment: str = Field(..., description="Human-readable risk summary.")
    explanation_tags: List[str] = Field(..., description="Explainability tags highlighting stylistic & linguistic markers.")
    stylometrics: StylometricFeatures
    model_scores: ModelScores
    latency_ms: float

class BatchPredictionResponse(BaseModel):
    total_articles: int
    fake_count: int
    real_count: int
    results: List[PredictionResponse]
    latency_ms: float

class BenchmarkMetricItem(BaseModel):
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    log_loss: float

class SampleArticle(BaseModel):
    id: str
    category: str  # 'real', 'fake', 'sensational'
    title: str
    text: str
    description: str

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    models_loaded: dict
    active_threshold: float

class GeminiEvaluateRequest(BaseModel):
    title: Optional[str] = Field(default="", description="The article headline.")
    text: str = Field(..., description="The article body or excerpt.")
    verdict: Optional[str] = Field(default=None, description="Local model verdict ('Likely Authentic' or 'Likely Misleading').")
    credibility_score: Optional[float] = Field(default=None, description="Local model credibility score.")

class GeminiEvaluateResponse(BaseModel):
    available: bool = Field(..., description="True if Gemini API was successfully called.")
    gemini_explanation: Optional[str] = Field(default=None, description="2-sentence plain-English cross-evaluation.")

