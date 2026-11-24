# Machine Learning Model Assets & Architecture

## Model Overview
This directory contains the serialized weights, pipelines, and configurations for the Fake News Detection Engine.

| Artifact | Size | Description | Benchmark Accuracy | Git Tracked |
|---|---|---|---|---|
| `model_1_svc.joblib` | 4.4 MB | Calibrated Linear Support Vector Classifier (LinearSVC with Platt Sigmoid calibration) | **99.03%** | Yes |
| `tfidf_union.joblib` | 4.2 MB | Scikit-learn `FeatureUnion` combining word n-grams (1,3) and char n-grams (3,5) | N/A (Feature Extractor) | Yes |
| `model_2_lgb.joblib` | 2.6 MB | LightGBM Gradient Boosted Decision Tree (175 features) | **99.69%** | Yes |
| `ensemble_config.json` | 237 B | Ensemble blending weights and optimal decision threshold | N/A (Config) | Yes |
| `svd_reducer.joblib` | 140.8 MB | `TruncatedSVD` (160 components) for dense dimension reduction | Component for Model 2 | Git LFS / External |
| `model_3_deberta/` | 283.8 MB | DeBERTa-v3-small Transformer model weights (`model.safetensors`) | 54.21% (Baseline) | Git LFS / External |

## Inference Engine Fallback Hierarchy
1. **Full Ensemble (99.69% Accuracy, 0.9999 ROC-AUC)**:
   - When all weights (including `svd_reducer.joblib`) are available, the inference engine extracts 15 stylometric features, transforms text with TF-IDF and SVD, and computes the weighted blend between Calibrated LinearSVC and LightGBM.
2. **High-Speed Standalone Engine (99.03% Accuracy, 0.9994 ROC-AUC)**:
   - Powered by `model_1_svc.joblib` and `tfidf_union.joblib` (<9 MB total).
   - Operates with sub-15ms latency without requiring the 140MB SVD matrix.
   - Ideal for serverless, edge, and standard GitHub deployments.

## Git Large File Storage (Git LFS)
Because GitHub enforces a **100 MB hard limit** on individual files:
- Files exceeding 100 MB (`svd_reducer.joblib` and `model.safetensors`) are ignored by default or tracked via `.gitattributes` with Git LFS.
- To push with Git LFS:
  ```bash
  git lfs install
  git lfs track "*.joblib"
  git lfs track "*.safetensors"
  ```
