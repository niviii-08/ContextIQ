# Probability Calibration Analysis Report

This report analyzes the calibration quality of trained models.
Well-calibrated probabilities are important when the model's
predicted probabilities will be used for decision-making.

## Calibration Metrics Summary

| Model | Brier Score | ECE | Interpretation |
|-------|-------------|-----|----------------|
| dummy_most_frequent | 0.2764 | 0.0000 | Excellent |
| logistic_regression | 0.2273 | 0.1992 | Poor |
| random_forest | 0.2179 | 0.1772 | Poor |
| xgboost | 0.2312 | 0.1905 | Poor |
| logistic_regression_calibrated | 0.1856 | 0.0178 | Excellent |

## Metric Definitions

### Brier Score
- Measures the mean squared difference between predicted probabilities
  and actual outcomes.
- Lower is better (0 = perfect, 0.25 = random for binary classification).
- Combines both calibration and refinement (discrimination).

### Expected Calibration Error (ECE)
- Weighted average of calibration error across probability bins.
- Lower is better (0 = perfectly calibrated).
- Focuses specifically on calibration quality, independent of discrimination.

## Interpretation for Forgetting-Risk Prediction

For forgetting-risk prediction, calibration matters because:
- Users may interpret a 70% risk as 'highly likely to forget'
- If the model is poorly calibrated, a 70% prediction might actually
  correspond to a 40% or 90% true risk
- Good calibration enables trustworthy probability-based decision making
- Threshold selection (e.g., 'flag tasks above 50% risk') depends on
  accurate probability estimates

## Detailed Bin Analysis - dummy_most_frequent

| Bin | Mean Predicted | Fraction Positive | Sample Count | Calibration Error |
|-----|----------------|-------------------|--------------|-------------------|
| 1 | 0.000 | 0.276 | 0 | 0.276 |
