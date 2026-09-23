# Forgetting Prediction ML System - Recruiter's Guide

This guide provides a comprehensive overview of the machine learning system for recruiters and technical evaluators to quickly understand the architecture, implementation quality, and capabilities.

## Quick Start for Evaluation

### 1. Run the Complete Pipeline

```bash
# Generate synthetic dataset and train all models
python -m ml.training.train
```

This single command executes the entire ML pipeline:
- Generates reproducible synthetic dataset
- Performs time-aware train/validation/test splitting
- Trains baseline (Dummy), Logistic Regression, Random Forest, and XGBoost models
- Runs time-series cross-validation
- Performs model selection using PR-AUC as primary metric
- Applies probability calibration
- Generates comprehensive evaluation artifacts

### 2. Inspect Trained Model

```bash
# Quick summary
python scripts/inspect_model.py

# Detailed feature information
python scripts/inspect_model.py --features

# Performance metrics
python scripts/inspect_model.py --metrics

# Preprocessing details
python scripts/inspect_model.py --preprocessing

# Everything
python scripts/inspect_model.py --full
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_integration.py -v          # End-to-end pipeline tests
pytest tests/test_dataset_generation.py -v    # Dataset reproducibility tests
pytest tests/test_ml_pipeline_and_inference.py -v  # ML component tests
```

### 4. View Generated Artifacts

After training, inspect the `artifacts/` directory:

- `model_bundle.joblib` - Trained model with preprocessing pipeline
- `metrics.json` - Complete performance metrics for all models
- `feature_metadata.json` - Feature contract and preprocessing details
- `performance_report.md` - Human-readable performance analysis
- `model_selection_report.md` - Detailed model comparison
- `calibration_report.md` - Probability calibration analysis
- Various PNG plots for visualization

## Architecture Overview

### Pipeline Components

```
ml/
├── data/
│   └── generate_dataset.py       # Reproducible synthetic data generation
├── features/
│   └── feature_spec.py            # Single source of truth for feature contract
├── preprocessing/
│   └── pipeline.py                # sklearn ColumnTransformer for preprocessing
├── training/
│   ├── config.py                  # Centralized hyperparameter configuration
│   ├── splits.py                  # Time-aware splitting logic
│   └── train.py                   # End-to-end training pipeline
├── evaluation/
│   ├── report.py                  # Plot and report generation
│   ├── model_comparison.py        # Statistical model comparison
│   └── calibration_analysis.py    # Detailed calibration analysis
└── explainability/
    └── explainer.py               # SHAP-based explanation generation
```

### Inference Service

```
app/
├── main.py                        # FastAPI application entry point
├── api.py                         # API route definitions
├── schemas.py                     # Pydantic request/response schemas
└── inference.py                   # Model loading and prediction logic
```

## Key Implementation Features

### 1. Reproducible Dataset Generation

**Location**: `ml/data/generate_dataset.py`

- **Fixed random seed**: All randomness uses `SEED = 42` from config
- **Dataset fingerprinting**: SHA-256 hash of dataset structure and content
- **Leakage prevention**: Assertions verify no target leakage in rolling features
- **Temporal validity**: Each row represents a prediction point with only prior information

**Verification**:
```bash
pytest tests/test_dataset_generation.py -v
```

### 2. Time-Aware Data Splitting

**Location**: `ml/training/splits.py`

- **Chronological split**: 70% train / 15% validation / 15% test by date
- **No leakage assertions**: Verifies no date overlap between splits
- **Walk-forward CV**: Time-series cross-validation for robustness estimates
- **User overlap**: Users appear across splits but with strictly later behavior

**Why this matters**: Behavioral data is sequential; random splits would leak future information.

### 3. Target Leakage Prevention

**Multiple layers of protection**:

1. **Feature construction**: Rolling historical features computed strictly chronologically
2. **Splitting**: Time-aware splits prevent future data in training
3. **Calibration**: Fit only on validation, never on test
4. **Preprocessing**: Fit on train only, reused at inference via saved artifact

**Verification**:
```bash
pytest tests/test_ml_pipeline_and_inference.py::test_chronological_split_no_date_overlap -v
```

### 4. Feature Preprocessing

**Location**: `ml/preprocessing/pipeline.py`

- **Numeric features**: Median imputation + optional StandardScaler (for LR)
- **Categorical features**: Most-frequent imputation + OneHot encoding
- **Unknown categories**: Handled gracefully at inference time
- **Missing values**: Imputed using statistics from training data

**Single source of truth**: Feature contract defined in `ml/features/feature_spec.py`

### 5. Model Training & Selection

**Models trained**:
1. **Dummy baseline** (most-frequent) - Establishes lower bound
2. **Logistic Regression** - Interpretable baseline with class weighting
3. **Random Forest** - Tree-based ensemble with balanced subsampling
4. **XGBoost** - Gradient boosting with scale_pos_weight for imbalance

**Selection criteria** (in order):
1. **PR-AUC** (Primary) - Best for imbalanced classification
2. **ROC-AUC** (Secondary) - Overall ranking quality
3. **F1** (Tertiary) - Thresholded performance
4. **Calibration quality** - Brier score improvement
5. **CV stability** - Lower variance across folds

### 6. Class Imbalance Handling

**Three-pronged approach**:

1. **Training-time weighting**:
   - LR/RF: `class_weight='balanced'` / `'balanced_subsample'`
   - XGBoost: `scale_pos_weight = #neg/#pos`

2. **Threshold tuning**: Operating threshold chosen to maximize F1 on validation

3. **Metric selection**: PR-AUC rather than accuracy prevents trivial majority-class solutions

### 7. Probability Calibration

**Methods evaluated**: Isotonic regression and sigmoid (Platt scaling)

**Selection**: Best method chosen by validation Brier score

**Why calibration matters**: Users interpret predicted probabilities literally; poor calibration leads to misinformed decisions.

**Artifacts**: `calibration_report.md`, `calibration_detailed.png`, `calibration_comparison.png`

### 8. Comprehensive Evaluation Metrics

**All models evaluated on**:
- Accuracy
- Precision  
- Recall
- F1 Score
- ROC-AUC
- **PR-AUC** (Primary metric)
- Brier Score (calibration)
- Confusion Matrix

**Cross-validation**: 5-fold walk-forward time-series CV on train+val

### 9. Explainability

**SHAP-based explanations**:
- **Global importance**: Mean absolute SHAP values across test set
- **Individual predictions**: Top-k features driving each prediction
- **Visualizations**: Beeswarm plots, waterfall charts

**Fallback**: Native feature importances if SHAP unavailable

**Causality disclaimer**: All explanations describe association, not causation.

## Which Metric Matters Most?

**PR-AUC (Average Precision) is the primary metric** because:

1. **Class imbalance**: Forgetting is the minority class (~28% in synthetic data)
2. **Cost asymmetry**: Missing a forgotten task (false negative) is more costly than false alarm
3. **Ranking focus**: We care about ranking riskiest tasks highest, not overall accuracy
4. **Robustness**: PR-AUC is invariant to class imbalance, unlike accuracy

**Why not accuracy?** A trivial "never forget" classifier achieves ~72% accuracy by doing nothing useful.

**Secondary metrics**:
- **ROC-AUC**: Overall discriminative power (tie-breaker)
- **F1**: Quality of chosen operating threshold
- **Recall**: Fraction of actual forgotten tasks flagged
- **Precision**: Trustworthiness of flagged tasks

## Test Coverage

### Test Categories

1. **Dataset Generation** (`test_dataset_generation.py`):
   - Reproducibility with same seed
   - Target leakage prevention
   - Chronological ordering
   - Fingerprint determinism

2. **ML Pipeline** (`test_ml_pipeline_and_inference.py`):
   - Splitting logic (chronological, no leakage)
   - Preprocessing (unknown categories, missing values)
   - Model loading and artifact integrity
   - Prediction validity (probability range, batch consistency)
   - Invalid input handling

3. **Integration** (`test_integration.py`):
   - End-to-end training flow
   - Model bundle loading and inference
   - Metrics completeness
   - Reproducibility

4. **Model & Inference** (`test_model_and_inference.py`):
   - Single/batch prediction consistency
   - Risk level mapping
   - Missing feature handling

### Running Tests

```bash
# All tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=ml --cov=app --cov-report=html
```

## Model Artifacts

### Model Bundle Structure

`artifacts/model_bundle.joblib` contains:

```python
{
    "model": ...,                       # Final (possibly calibrated) model
    "raw_model": ...,                    # Uncalibrated model for SHAP
    "preprocessor": ...,                  # Fitted ColumnTransformer
    "model_name": "xgboost",             # Selected model type
    "model_version": "1.1.0",            # Semantic version
    "threshold": 0.215,                  # F1-tuned decision threshold
    "calibrated": True,                  # Whether calibration was applied
    "calibration_method": "isotonic",    # Method used
    "feature_names_raw": [...],          # Input feature names
    "feature_names_transformed": [...],  # Post-preprocessing names
    "categorical_features": [...],       # Categorical feature list
    "numeric_features": [...],           # Numeric feature list
    "background_sample": ...,            # SHAP background data
}
```

### Inference Service

**Loading**: The inference service loads the trained artifact at startup:

```python
from app.inference import ForgettingPredictor

predictor = ForgettingPredictor.instance()  # Loads model_bundle.joblib
result = predictor.predict_single(task_dict)
```

**No retraining**: Predictions always use the trained model, never retrain.

## API Integration

### HTTP Endpoint

```bash
POST /api/v1/predictions/forgetting
Content-Type: application/json

{
  "task_category": "Academic",
  "priority": "HIGH",
  "location": "Campus",
  "weekday": 2,
  "hour": 14,
  "deadline_distance_hours": 18.0,
  "previous_completion_count": 12,
  "previous_forgetting_count": 8,
  "historical_completion_rate": 0.4,
  "historical_forgetting_rate": 0.55,
  "task_frequency": 0.3,
  "tasks_today": 5,
  "interruptions_today": 4,
  "recent_context_switches": 6,
  "avg_interruption_duration": 8.5,
  "avg_session_duration": 22.0
}
```

### Response

```json
{
  "task": null,
  "prediction_probability": 0.6234,
  "risk_level": "HIGH",
  "model_version": "1.1.0",
  "top_features": [
    "Historical forgetting rate is increasing the estimated forgetting risk (impact: 0.234)",
    "Interruptions today is increasing the estimated forgetting risk (impact: 0.156)",
    "Historical completion rate is decreasing the estimated forgetting risk (impact: -0.123)"
  ]
}
```

## Hyperparameter Configuration

**Location**: `ml/training/config.py`

All hyperparameters are centralized for easy inspection and modification:

```python
@dataclass
class XGBoostParams:
    n_estimators: int = 500
    max_depth: int = 5
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    # ... etc
```

**Versioning**: Model version tracked separately from hyperparameters for reproducibility.

## Documentation

### Technical Documentation

- `docs/FEATURE_ENGINEERING.md` - Feature construction details
- `docs/MODEL_METHODOLOGY.md` - Modeling approach and results
- `docs/EVALUATION.md` - Evaluation metrics and analysis
- `docs/API_CONTRACT.md` - Complete API specification

### Generated Reports

- `artifacts/performance_report.md` - Training run performance
- `artifacts/model_selection_report.md` - Model comparison analysis
- `artifacts/calibration_report.md` - Calibration quality analysis

## Code Quality Indicators

### Design Patterns

- **Single source of truth**: Feature contract defined once, imported everywhere
- **Dependency injection**: Preprocessor injected into training and inference
- **Factory pattern**: Model builders for CV and training
- **Strategy pattern**: Multiple calibration methods evaluated

### Testing

- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end pipeline testing
- **Property-based tests**: Reproducibility and invariant testing
- **Coverage**: Comprehensive test coverage of critical paths

### Error Handling

- **Graceful degradation**: SHAP failures fall back to native importances
- **Validation**: Input validation at API boundaries
- **Assertions**: Runtime checks for data invariants (leakage, ordering)

## Performance Characteristics

### Training Time

- **Dataset generation**: ~5-10 seconds for 100 users × 95 days
- **Model training**: ~30-60 seconds for all 4 models
- **Total pipeline**: ~1-2 minutes on modern hardware

### Inference Latency

- **Single prediction**: < 10ms
- **Batch prediction**: ~1ms per prediction
- **Model loading**: ~100-500ms (one-time at startup)

### Memory Usage

- **Model bundle**: ~5-15 MB depending on model type
- **Dataset**: ~10-20 MB for synthetic dataset
- **Training peak**: ~500 MB - 1 GB

## Limitations & Ethical Considerations

### Known Limitations

1. **Synthetic data**: Current evaluation uses synthetic data; real-world performance may differ
2. **Behavioral assumption**: Assumes historical patterns predict future behavior
3. **No causal claims**: SHAP explanations describe correlation, not causation
4. **Static features**: Does not incorporate real-time context or external factors

### Ethical Use

- **Not diagnostic**: This is a behavioral prediction tool, not a medical/psychological diagnostic
- **Probability interpretation**: Outputs are probabilistic estimates, not certainties
- **Human oversight**: Should inform, not replace, human decision-making
- **Bias potential**: May reflect biases present in training data

## Recruiter Evaluation Checklist

Use this checklist to evaluate the ML system:

- [ ] Training runs successfully with `python -m ml.training.train`
- [ ] All artifacts generated in `artifacts/` directory
- [ ] Model inspection tool works: `python scripts/inspect_model.py`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Performance report shows PR-AUC > baseline
- [ ] Calibration report shows reasonable ECE (< 0.15)
- [ ] Model selection report justifies chosen model
- [ ] Feature metadata shows preprocessing details
- [ ] SHAP plots are generated and interpretable
- [ ] Inference service loads trained model (no retraining)
- [ ] API accepts valid requests and returns proper responses
- [ ] Invalid inputs are handled gracefully
- [ ] Code is well-documented and modular
- [ ] Configuration is centralized and versioned
- [ ] Tests cover critical paths

## Contact & Support

For questions about this ML system:
- Review the technical documentation in `docs/`
- Inspect generated reports in `artifacts/`
- Run tests to verify functionality: `pytest tests/ -v`
- Use the inspection tool: `python scripts/inspect_model.py --full`
