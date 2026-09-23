# Forgetting-Risk Prediction — Performance Report

_Generated 2026-08-20T03:52:09_

## Run Metadata

- **Model version:** `1.1.0`
- **Dataset version:** `1.0.0`
- **Dataset fingerprint (SHA-256, 16):** `81d87490610d3a36`
- **Selected model:** `logistic_regression`
- **Training duration:** 45.7s

## Which Metric Matters and Why

Model selection is driven primarily by PR-AUC (Average Precision) because for forgetting-risk prediction — a class-imbalanced problem where the positive class (forgotten) is the minority and the cost of missing a forgotten task (false negative) is high for the user. ROC-AUC is a secondary tie-breaker for ranking quality, and F1 confirms thresholded quality. Accuracy is intentionally de-prioritized because a trivial 'never-forget' majority-class classifier achieves ~72.2% accuracy by doing nothing useful.

Concretely:

- **PR-AUC (Average Precision)** ← PRIMARY. Summarizes the whole precision/recall trade-off curve; invariant to class imbalance and directly rewards ranking the *riskiest* tasks first.
- **ROC-AUC** ← SECONDARY tie-breaker. Measures overall ranking discriminative power across all operating points.
- **F1** ← tertiary. Quality of the chosen *operating threshold* (after threshold tuning on val).
- **Recall** ← operational safety net. The fraction of actually-forgotten tasks that were flagged.
- **Precision** ← operational trust. Fraction of flagged tasks that actually were forgotten.
- **Accuracy** ← intentionally de-prioritized; misleading under class imbalance.

## Class Balance

- Positive (forgotten=1): `27.75%`
- Negative (forgotten=0): `72.25%`

## Chronological Split Summary

| Split | N rows | N users | Date range | Forget rate |
|-------|--------|---------|------------|-------------|
| train | 34397 | 100 | 2025-01-01 → 2025-03-07 | 27.74% |
| val | 7357 | 100 | 2025-03-08 → 2025-03-21 | 27.93% |
| test | 7875 | 100 | 2025-03-22 → 2025-04-05 | 27.64% |

> Split rule: global chronological by date. 70% train / 15% val / 15% test.
> A user may appear in all three splits but *always* with behaviour strictly later in val/test than in train (no time leakage).

## Candidate Models — Held-Out Test Metrics

| Model | Acc | Precision | Recall | F1 | ROC-AUC | **PR-AUC** | Brier |
|-------|-----|-----------|--------|----|---------|------------|-------|
| dummy_most_frequent | 0.724 | 0.000 | 0.000 | 0.000 | 0.500 | 0.276 | 0.276 |
| **logistic_regression** | 0.572 | 0.355 | 0.674 | 0.465 | 0.658 | **0.445** | 0.227 |
| random_forest | 0.548 | 0.349 | 0.734 | 0.473 | 0.657 | 0.437 | 0.218 |
| xgboost | 0.477 | 0.319 | 0.785 | 0.454 | 0.626 | 0.406 | 0.231 |

## Final Selected Model: `logistic_regression`

| Metric | Value |
|--------|-------|
| accuracy | 0.5813 |
| precision | 0.3596 |
| recall | 0.6587 |
| f1 | 0.4652 |
| roc_auc | 0.6574 |
| pr_auc | 0.4312 |
| brier_score | 0.1856 |
| specificity | 0.5518 |
| threshold (max F1 on val, post-calibration) | 0.235 |
| calibration applied? | True (isotonic) |

### Confusion Matrix (selected model, test)

| | Predicted Not Forgotten | Predicted Forgotten |
|---|--------------------------|----------------------|
| Actual Not Forgotten | **3144** (TN) | 2554 (FP) |
| Actual Forgotten     | 743 (FN) | **1434** (TP) |

## Time-Series Cross-Validation (walk-forward, 5 folds on train+val)

| Model | Fold | PR-AUC ± std | ROC-AUC ± std | F1 ± std |
|-------|------|--------------|---------------|----------|
| logistic_regression | 5 | 0.4430 ± 0.0114 | 0.6588 ± 0.0017 | 0.4757 ± 0.0057 |
| random_forest | 5 | 0.4327 ± 0.0127 | 0.6494 ± 0.0045 | 0.4675 ± 0.0067 |
| xgboost | 5 | 0.3997 ± 0.0199 | 0.6215 ± 0.0172 | 0.4560 ± 0.0058 |

> Walk-forward time-series CV avoids standard (shuffled) K-fold which is known to leak future information in sequential/behavioral data. Each CV fold is a strictly later date window than its train portion.

## Probability Calibration

- Methods evaluated: ['isotonic', 'sigmoid']
- Calibration applied? True
- Chosen method: isotonic

## Class Imbalance Handling

- **Training-time weighting:** LR/RF use `class_weight='balanced'` / `'balanced_subsample'`. XGBoost uses `scale_pos_weight = #neg/#pos`.
- **Inference-time threshold tuning:** operating threshold is chosen to MAXIMIZE F1 on the validation split, rather than naively using 0.5. This is especially impactful under imbalance.
- **Model selection metric:** PR-AUC (Average Precision) rather than accuracy, so that a 'trivial' majority-class baseline cannot look good by doing nothing.

## Feature Metadata

See `artifacts/feature_metadata.json` for the full contract: per-feature median imputation values, StandardScaler means/scales (for LR path), one-hot category lists, and human-readable descriptions.

## Target-Leakage Prevention

1. **Feature construction** — Rolling historical counters (`previous_forgetting_count`, `historical_completion_rate`, etc.) are computed per user in strict chronological order; a row's own label is only added to counters *after* the row is emitted. Assertions in `ml/data/generate_dataset.py` verify this invariant.
2. **Splitting** — Strict chronological split by global date with overlap assertions in `ml/training/splits.py`. Standard K-fold would leak, so it is replaced with walk-forward time-series CV.
3. **Calibration & threshold tuning** — Both are fit *only* on the validation split; the test split is touched exactly once for final reporting.
4. **Preprocessing** — Preprocessor is fit on train (or train-fold) only; fitted medians/scales/one-hot vocabularies are re-used at serve time via the persisted `model_bundle.joblib`.

## Artifact Inventory

- `artifacts/model_bundle.joblib` — Final calibrated model, raw model, fitted preprocessor, threshold, feature lists, SHAP background.
- `artifacts/feature_metadata.json` — Feature contract (imputer medians, StandardScaler params, one-hot vocab, descriptions).
- `artifacts/metrics.json` — Machine-readable full metrics (candidates, CV, final).
- `artifacts/confusion_matrix.png`
- `artifacts/roc_curve.png` (all candidates overlaid)
- `artifacts/precision_recall_curve.png` (all candidates)
- `artifacts/feature_importance.png` (MDI / |coef|)
- `artifacts/calibration_plot.png`
- `artifacts/shap_summary_bar.png` (global mean |SHAP|)
- `artifacts/shap_beeswarm.png` (global SHAP value distribution)
- `artifacts/shap_individual_waterfalls.png` (LOW/MEDIUM/HIGH individual examples explained)
- `artifacts/performance_report.md` (this document)
