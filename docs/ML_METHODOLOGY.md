# ContextIQ ML Methodology

## Prediction Problem

The forgetting service estimates `P(task will be forgotten | information available before prediction time)`. The target is binary `will_forget`, derived from whether a task eventually reaches the forgotten state.

This target is useful because it supports proactive attention while a task is still actionable. It is not a diagnosis, trait assessment, or statement of intent.

## Why These Models

- **Logistic Regression** provides a fast, interpretable baseline for mostly additive behavioural signals.
- **Random Forest** tests non-linear interactions without requiring manual interaction terms.
- **XGBoost** tests a strong gradient-boosting approach for tabular data and is a natural candidate when real data becomes richer.

The selected model is ranked by PR-AUC, then ROC-AUC and F1. Accuracy is not the primary metric because the forgotten class is a minority class.

## Validation and Leakage Prevention

- Data is split chronologically into train, validation, and test windows.
- Walk-forward time-series cross-validation is used for stability estimates.
- Historical features are computed before each task's timestamp with strict cutoffs.
- The current task's final status is excluded from its inputs.
- User-level identifiers and post-outcome fields are excluded from model features.
- Dataset generation includes target-leakage assertions.

## Preprocessing

Numeric features use median imputation and, for the linear path, standard scaling. Categorical features use most-frequent imputation and one-hot encoding. The fitted preprocessor is saved with the model so inference uses the exact training transformation.

## Imbalance, Thresholds, and Calibration

Class weighting is used for Logistic Regression and Random Forest; XGBoost uses a negative/positive class weight. The operating threshold is tuned on validation data for F1 instead of assuming `0.5`. Brier score and calibration methods are evaluated because the API exposes a probability, not only a ranking.

## Explainability

SHAP or a model-native fallback produces ranked feature contributions for individual predictions and aggregate importance artifacts. These are model associations. They do not establish causality and should be presented with the input data and model version.

## Artifact Contract

A served bundle includes the fitted model, raw model, preprocessor, feature lists, transformed feature names, threshold, calibration state, and model version. The inference service rejects missing bundle fields, incompatible model versions, malformed feature metadata, invalid probability matrices, and non-finite or out-of-range probabilities.

## Current Evidence and Limits

The available benchmark is synthetic and reproducible, so its metrics demonstrate pipeline behaviour rather than real-world validity. Model performance, calibration, fairness, drift, and usefulness must be re-evaluated on consented representative data before deployment.

See [forgetting-ml/docs/MODEL_METHODOLOGY.md](../forgetting-ml/docs/MODEL_METHODOLOGY.md), [EVALUATION.md](../forgetting-ml/docs/EVALUATION.md), and [FEATURE_DICTIONARY.md](FEATURE_DICTIONARY.md).
