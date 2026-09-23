# Model Selection & Comparison Report

_Generated 2026-08-20T03:52:09_

## Model Rankings (Test Set)

| Rank | Model | PR-AUC | ROC-AUC | F1 | Accuracy | Brier |
|------|-------|--------|---------|----|----------|-------|
| 1 | logistic_regression | 0.4451 | 0.6583 | 0.4651 | 0.5716 | 0.2273 |
| 2 | random_forest | 0.4369 | 0.6574 | 0.4728 | 0.5478 | 0.2179 |
| 3 | xgboost | 0.4055 | 0.6265 | 0.4536 | 0.4772 | 0.2312 |
| 4 | dummy_most_frequent | 0.2764 | 0.5000 | 0.0000 | 0.7236 | 0.2764 |

## Pairwise Differences

### dummy_most_frequent_vs_logistic_regression
- Difference: -0.1686
- Relative improvement: -37.89%
- Better model: logistic_regression

### dummy_most_frequent_vs_random_forest
- Difference: -0.1604
- Relative improvement: -36.72%
- Better model: random_forest

### dummy_most_frequent_vs_xgboost
- Difference: -0.1291
- Relative improvement: -31.83%
- Better model: xgboost

### logistic_regression_vs_random_forest
- Difference: 0.0082
- Relative improvement: 1.88%
- Better model: logistic_regression

### logistic_regression_vs_xgboost
- Difference: 0.0395
- Relative improvement: 9.75%
- Better model: logistic_regression

### random_forest_vs_xgboost
- Difference: 0.0313
- Relative improvement: 7.73%
- Better model: random_forest

## Cross-Validation Stability Analysis

### logistic_regression
- PR-AUC: 0.4430 ± 0.0114 (n=5)
- Range: [0.4276, 0.4586]
- Coefficient of variation: 2.57%
- ROC-AUC: 0.6588 ± 0.0017

### random_forest
- PR-AUC: 0.4327 ± 0.0127 (n=5)
- Range: [0.4172, 0.4511]
- Coefficient of variation: 2.94%
- ROC-AUC: 0.6494 ± 0.0045

### xgboost
- PR-AUC: 0.3997 ± 0.0199 (n=5)
- Range: [0.3848, 0.4376]
- Coefficient of variation: 4.99%
- ROC-AUC: 0.6215 ± 0.0172

## Selection Rationale

**Selected model: logistic_regression**

Selection criteria (in order of priority):
1. **PR-AUC (Average Precision)** - Primary metric for imbalanced classification
2. **ROC-AUC** - Secondary metric for overall ranking quality
3. **F1 Score** - Tertiary metric for thresholded performance
4. **Calibration quality** - Brier score improvement after calibration
5. **Cross-validation stability** - Lower variance across folds preferred

## Model Trade-offs

### logistic_regression
- **Strengths:**
  - Best PR-AUC (0.4451)
  - Best ROC-AUC (0.6583)
- **Weaknesses:**

### random_forest
- **Strengths:**
  - Best F1 (0.4728)
  - Best calibration (lowest Brier: 0.2179)
- **Weaknesses:**

### xgboost
- **Strengths:**
- **Weaknesses:**

### dummy_most_frequent
- **Strengths:**
- **Weaknesses:**
  - Lowest PR-AUC
  - Poorest calibration
