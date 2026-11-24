import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.main import app

client = TestClient(app)

def test_web_ui_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "CrediNews AI" in response.text
    assert "text/html" in response.headers.get("content-type", "")

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "models_loaded" in data
    assert "active_threshold" in data

def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    ensemble = next((m for m in data if "Ensemble" in m["model_name"]), None)
    assert ensemble is not None
    assert ensemble["accuracy"] > 0.99

def test_samples_endpoint():
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 4
    categories = [s["category"] for s in samples]
    assert "real" in categories
    assert "fake" in categories

def test_predict_real_news():
    payload = {
        "title": "Municipal Transit Board Approves Clean Fleet Modernization Plan",
        "text": "The regional metropolitan transport authority approved a multi-year fleet transition schedule on Wednesday. Regional transit operators will integrate eighty low-emission hybrid buses.",
        "threshold": 0.50
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert "credibility_score" in data
    assert "fake_probability" in data
    assert "real_probability" in data
    assert data["credibility_score"] >= 60.0
    assert "stylometrics" in data
    assert "model_scores" in data
    assert data["is_fake"] is False

def test_predict_fake_news():
    payload = {
        "title": "UNBELIEVABLE DISCOVERY: Secret Galactic Frequencies Detected in Desert Caverns!!",
        "text": "You will not believe what researchers discovered deep underground! Distribute this information immediately before authorities suppress the channel!!",
        "threshold": 0.50
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert data["is_fake"] is True
    assert data["credibility_score"] < 40.0
    assert data["fake_probability"] >= 0.60

def test_batch_prediction():
    payload = {
        "articles": [
            {
                "title": "Municipal Transit Board Approves Fleet Plan",
                "text": "The regional metropolitan transport authority approved a multi-year fleet transition schedule on Wednesday."
            },
            {
                "title": "UNBELIEVABLE MIRACLE CLAIM YOU MUST SHARE!!",
                "text": "Secret formula cures everything overnight! Authorities hate this secret!"
            }
        ]
    }
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_articles"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["is_fake"] is False
    assert data["results"][1]["is_fake"] is True

def test_predict_fake_news_with_quotes_and_attribution():
    """
    Regression test: ensures fake news with quotes and journalistic patterns
    is correctly classified as fake instead of being incorrectly overridden to real.
    """
    payload = {
        "title": "Secret cures hidden by big pharmaceutical corporations",
        "text": "A retired practitioner claimed 'kitchen spices eliminate diabetes within three days.' Major companies reportedly filed lawsuits to silence the discovery.",
        "threshold": 0.50
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_fake"] is True
    assert data["fake_probability"] >= 0.50
    assert "Fake" in data["verdict"]

def test_predict_real_world_genuine_news():
    """
    Ensures standard genuine news without wire datelines is correctly classified as real.
    """
    payload = {
        "title": "European Central Bank Lowers Benchmark Interest Rate by 25 Basis Points",
        "text": "Policymakers in Frankfurt concluded their monetary policy session on Thursday by trimming the deposit facility rate to three percent, citing moderating wage pressures across the eurozone.",
        "threshold": 0.50
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_fake"] is False
    assert data["real_probability"] >= 0.50
    assert "Real" in data["verdict"]

def test_gemini_evaluate_graceful_fallback():
    """
    Ensures gemini-evaluate endpoint returns gracefully when no GEMINI_API_KEY is configured.
    """
    payload = {
        "title": "Municipal Transit Board Approves Fleet Plan",
        "text": "The regional transit operators will integrate eighty low-emission hybrid buses.",
        "verdict": "Likely Authentic",
        "credibility_score": 98.0
    }
    response = client.post("/api/v1/gemini-evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    # In test environment without GEMINI_API_KEY, available should be False and no crash
    assert data["available"] is False
    assert data["gemini_explanation"] is None


