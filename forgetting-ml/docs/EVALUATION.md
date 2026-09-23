# Evaluation

## Metrics computed

For every candidate model, the following are computed on the
chronological test set (never seen during training or threshold
tuning):

- **Accuracy** — overall correctness; reported but explicitly not used
  as the selection criterion (see rationale below).
- **Precision** — of tasks predicted "forgotten", how many actually were.
- **Recall** — of tasks actually forgotten, how many were caught.
- **F1** — harmonic mean of precision/recall; used to tune the decision
  threshold.
- **ROC-AUC** — ranking quality across all thresholds, insensitive to
  the prior class balance.
- **PR-AUC** — ranking quality focused on the positive (forgotten)
  class; the **primary model-selection metric**, since it is more
  informative than ROC-AUC under class imbalance.
- **Brier score** — mean squared error between predicted probability and
  the actual binary outcome; the metric used to evaluate and select
  calibration.
- **Confusion matrix** — raw counts of true/false positives/negatives at
  the tuned threshold.

All numbers in `artifacts/metrics.json` come directly from a real
training run (`python -m ml.training.train`) against the generated
dataset — none are hand-entered or estimated.

## Why accuracy is not the selection criterion

The dataset's positive class (`forgotten=1`) prevalence is ~27.6%. A
degenerate classifier that always predicts "not forgotten" would score
roughly **72% accuracy** while providing zero useful signal. All three
trained models score notably *lower* than that naive baseline on raw
accuracy at their tuned thresholds (which favor recall over accuracy) —
this is expected and correct given the F1-tuned threshold, and precisely
why accuracy is reported for completeness but PR-AUC drives selection.

## Class imbalance strategy (documented decision)

1. **Class weighting** (`class_weight="balanced"` / `scale_pos_weight`)
   during training, so the loss function does not implicitly favor the
   majority class.
2. **Threshold tuning** on the validation set: thresholds from 0.05 to
   0.95 are swept, and the threshold maximizing F1 is selected. This
   threshold is re-tuned after calibration, because isotonic calibration
   changes the meaning of the probability scale.
3. **No blind oversampling.** SMOTE-style synthetic oversampling was
   considered and rejected for this dataset: class weighting already
   achieves a reasonable precision/recall trade-off, and oversampling on
   top of an already-synthetic dataset would risk amplifying artifacts
   of the generative process rather than improving real signal capture.

This is a moderate imbalance (not the 1:100+ imbalance seen in fraud or
rare-disease detection), so weighting + threshold tuning was judged
sufficient without resampling.

## Validation strategy (why chronological, not random)

See `docs/MODEL_METHODOLOGY.md` for full detail. In short: a random
train/test split would let the model be evaluated on rows that
chronologically precede some of its training data. Because several
features are rolling historical aggregates, this constitutes leakage of
future-derived summary statistics into the "past" evaluation set. The
chronological split (train on the first ~70% of days, validate on the
next ~15%, test on the final ~15%) avoids this and mirrors real
production usage: predicting forward in time using only what has already
happened.

## Calibration evaluation

- Calibration was assessed via **Brier score** (lower is better) and a
  **reliability diagram** (`artifacts/calibration_plot.png`), comparing
  mean predicted probability to observed frequency of the positive class
  within each probability bin (10 quantile bins).
- Isotonic regression calibration was applied because it strictly
  improved the test-set Brier score (0.2264 → 0.1813).
- **Known limitation**: the isotonic calibrator is fit on the validation
  set, and the operating threshold is *also* re-tuned on that same
  validation set post-calibration. Using the same split for both
  calibration fitting and threshold selection is mildly optimistic —
  in a stricter production setup, calibration and threshold tuning
  would each use independent held-out slices, or a dedicated third
  "calibration" split would be carved out of the chronological
  timeline. This is flagged here rather than silently accepted.

## Threshold behavior after calibration

Calibration remaps the probability distribution (isotonic regression is
a monotonic but non-linear transform), so the F1-optimal threshold moved
from **0.435** (raw Logistic Regression scores) to **0.215** (calibrated
scores). This is expected and not a modeling error — the *ranking* of
tasks by risk is preserved by calibration, but the *absolute* probability
values that correspond to a given operating point change. Any downstream
consumer relying on a fixed threshold must always use the threshold
value shipped alongside the specific model version
(`model_bundle["threshold"]` / `metrics.json`), never a hardcoded
constant.

## What "risk_level" means

The `risk_level` returned by the API buckets the calibrated probability
into three bands for convenience:

| Band | Probability range |
|---|---|
| LOW | `< 0.33` |
| MEDIUM | `0.33 – 0.66` |
| HIGH | `>= 0.66` |

These cut points are fixed, human-interpretable thresholds on the
0–1 probability scale — they are independent of (and coarser than) the
F1-optimized decision threshold used internally, which exists only to
support binary classification metrics in this report.

## Limitations of this evaluation

- All metrics describe performance on **synthetic data** generated by a
  known sigmoid process. They demonstrate that the pipeline correctly
  recovers a moderately noisy synthetic signal — they are **not** a
  forecast of real-world performance.
- No real user data, and no A/B or online evaluation, has been performed.
- The chronological split uses simulated dates from a single synthetic
  95-day window; real deployments should re-validate with rolling-origin
  or walk-forward validation across multiple time windows as more data
  accumulates.
- Sensitive subgroup / fairness analysis (e.g. across task categories or
  usage-frequency deciles) has not been performed here and should be
  part of any pre-production readiness review.

If you are experiencing challenges related to memory, attention, or
task management that are affecting your wellbeing, this tool is not a
substitute for professional guidance — consider speaking with a
qualified professional.
