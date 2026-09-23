# Model Methodology

## Problem statement

Estimate `P(task will be forgotten | information available before
prediction time)` for a single task instance. This is a **behavioural
prediction system** built on historical patterns of task completion and
forgetting. It is explicitly **not** a psychological or medical
diagnostic system, and its outputs must never be represented as clinical
assessments (e.g. of ADHD, memory disorders, or any condition).

## Dataset

Synthetic, reproducible (fixed seed = 42) behavioural dataset:

- **100 users**, simulated over **95 days**
- **49,779 task observations** (prediction points)
- Overall forgetting rate: **~27.6%** (class imbalance — see below)

Each user has latent behavioural traits (forgetfulness tendency,
organisation tendency, typical daily task load, typical interruption
load, typical session duration) that are **not** exposed directly as
features. Instead, these traits shape emergent, observable behavioural
signals (historical completion/forgetting rates, interruption counts,
etc.) that accumulate over time — mirroring how a real system would only
ever observe behaviour, not underlying psychological traits.

The label for each task is generated from a weighted combination of
~14 signals (user trait, category, priority, historical rates, deadline
distance, interruptions, context switches, session duration, weekday,
location, plus Gaussian noise) passed through a sigmoid. No single
feature determines the outcome — see `docs/FEATURE_ENGINEERING.md` and
the correlation check below.

**Correlation sanity check** (Pearson correlation with target, computed
on the full dataset): the strongest single-feature correlation is
`historical_forgetting_rate` / `historical_completion_rate` at
**~0.24**, confirming the target is not trivially determined by any one
input.

## Data leakage prevention

See `docs/FEATURE_ENGINEERING.md` for full detail. In summary: all
"historical" and "previous" features are computed from rolling counters
updated **after** each row is finalized, so a row's own outcome never
leaks into its own features or into any other row's features out of
temporal order.

## Validation strategy

**Chronological (time-aware) split**, not a random shuffle:

- Train: first ~70% of calendar days (34,564 rows)
- Validation: next ~15% of days (7,256 rows)
- Test: final ~15% of days (7,959 rows)

This mirrors real deployment: the model is always evaluated on behaviour
that occurred strictly after everything it was trained on. A random
shuffle split was deliberately avoided because rolling historical
features computed later in a user's timeline implicitly summarize
earlier behaviour; evaluating on randomly-selected "past" rows after
training on "future" rows would be optimistic and unrealistic.

## Class imbalance handling

Positive class (`forgotten=1`) prevalence is **~27.6%** — a real but
moderate imbalance, not extreme. Strategy used (documented choice, not
blind oversampling):

1. `class_weight="balanced"` for Logistic Regression and Random Forest.
2. `scale_pos_weight` (ratio of negative to positive class counts) for
   XGBoost.
3. **Threshold tuning**: instead of assuming a 0.5 decision threshold,
   the operating threshold is swept over `[0.05, 0.95]` on the
   validation set to maximize F1. This threshold is re-tuned after
   calibration, since isotonic calibration remaps the probability scale
   and a threshold selected on raw scores would no longer be meaningful.

Oversampling (e.g. SMOTE) was deliberately **not** used, since with
class weighting already achieving reasonable recall/precision balance,
synthetic oversampling on top of an already-synthetic dataset would risk
compounding unrealistic artifacts without a clear benefit.

## Models trained

| Model | Notes |
|---|---|
| Logistic Regression | Baseline; scaled numeric features; `class_weight="balanced"` |
| Random Forest | 300 trees, `max_depth=10`, `min_samples_leaf=20`, `class_weight="balanced"` |
| XGBoost | 300 rounds, `max_depth=5`, `learning_rate=0.05`, subsample/colsample 0.8, `scale_pos_weight` |

### Test-set results (chronological holdout, thresholds tuned on validation)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier |
|---|---|---|---|---|---|---|---|
| Logistic Regression | 0.569 | 0.346 | 0.706 | 0.464 | 0.663 | 0.424 | 0.226 |
| Random Forest | 0.547 | 0.335 | 0.726 | 0.459 | 0.659 | 0.422 | 0.222 |
| XGBoost | 0.574 | 0.340 | 0.648 | 0.446 | 0.639 | 0.405 | 0.214 |

All three models land in a similar performance band — expected, since
the signal-to-noise ratio was intentionally kept moderate when
generating the synthetic data (real forgetting behaviour is genuinely
noisy). None of the three dominates on every metric, which is itself a
realistic outcome worth reporting rather than a defect.

## Model selection strategy

**Selection is not accuracy-based.** With a ~72/28 class split, a
trivial "always predict not-forgotten" classifier would already score
~72% accuracy while being useless. Instead, models are ranked by:

1. **PR-AUC** (primary) — most informative under class imbalance, since
   it focuses on precision/recall trade-offs for the minority
   (forgotten) class rather than being dominated by the majority class.
2. **ROC-AUC** (tie-break)
3. **F1 at the tuned threshold** (second tie-break)

**Selected model: Logistic Regression** (highest PR-AUC at 0.424).

### Trade-offs across models (documented, not just asserted)

- **Logistic Regression**: best PR-AUC and ROC-AUC among the three;
  fully interpretable coefficients; fastest to train/serve; slightly
  higher Brier score before calibration (but calibration fixes this — see
  below). Assumes roughly additive/linear effects, which given the
  moderate, mostly-monotonic feature relationships in this domain turned
  out to be a reasonable fit.
- **Random Forest**: comparable PR-AUC/ROC-AUC to Logistic Regression,
  slightly better raw Brier score, and captures non-linear interactions
  without manual feature crosses. More expensive to serve and less
  directly interpretable (relies on impurity-based feature importance
  rather than coefficients).
- **XGBoost**: lowest PR-AUC/ROC-AUC of the three here, but the lowest
  Brier score before any calibration was applied — its native
  probability outputs were already the best-calibrated out of the box.
  Typically the strongest option on larger/more complex real-world
  behavioural datasets with richer interaction effects; underperformed
  the simpler models slightly on this particular synthetic dataset,
  which is a legitimate and reportable finding rather than a modeling
  error.

Given comparable discrimination across all three and Logistic
Regression's edge on the primary selection metric plus its
interpretability advantage, it was selected as the production model for
this iteration. This is not a claim that linear models are always
superior — with real, richer data XGBoost or Random Forest may well
outperform once genuine non-linear interaction effects are present.

## Probability calibration

Because the model output is used as a risk **probability** (not just a
ranking), calibration was assessed and corrected:

- **Method**: isotonic regression via `CalibratedClassifierCV` fit on
  the validation set, wrapping the already-trained model
  (`sklearn.frozen.FrozenEstimator`) so the base model is not
  re-trained.
- **Result**: Brier score improved from **0.2264 (uncalibrated)** to
  **0.1813 (calibrated)** on the test set → calibration was applied.
- The `calibration_plot.png` in `artifacts/` shows predicted probability
  vs. observed frequency on the test set, binned by quantile; the
  calibrated model tracks the diagonal reasonably closely across bins.

### Final selected-model test metrics (after calibration + re-tuned threshold)

| Metric | Value |
|---|---|
| Accuracy | 0.530 |
| Precision | 0.331 |
| Recall | 0.762 |
| F1 | 0.462 |
| ROC-AUC | 0.661 |
| PR-AUC | 0.411 |
| Brier score | 0.181 |
| Threshold | 0.215 |

Note the threshold moved substantially (0.435 → 0.215) after
calibration remapped the probability scale, and recall increased
markedly (0.706 → 0.762) at the cost of precision and raw accuracy —
consistent with a threshold re-tuned to maximize F1 on a
calibration-remapped probability distribution. This is a known,
documented limitation: see `docs/EVALUATION.md`.

## Limitations

- **This dataset is synthetic.** Reported metrics describe how well the
  models recover a synthetic, sigmoid-generated relationship — they say
  nothing about performance on real user behaviour, and **must not** be
  quoted as expected real-world performance.
- Real behavioural data will have different noise characteristics,
  different feature interactions, non-stationary user behaviour (drift),
  and almost certainly a different class balance.
- The model captures **association**, not causation (see
  `docs/EVALUATION.md` and the explainability output format).
- Retraining, revalidation, and recalibration against real production
  data is required before any real-world deployment decision is made
  using this model's outputs.
