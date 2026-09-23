# Intelligence Engine

## Scope

This document covers `app/insight_engine.py`, `app/ranking.py`,
`app/recommendations.py`, and `app/daily_summary.py`.

None of these modules perform prediction, probability estimation, or
association mining. They consume already-computed structured results
(`ForgettingPrediction`, `ContextInsight`, `Association`, `BehaviourMetric`)
and interpret them deterministically.

## Insight detection (`insight_engine.py`)

| Detector | Trigger | Insight type |
|---|---|---|
| `detect_frequent_forgetting` | `previous_forgetting_count >= 3` | `frequent_forgetting` |
| `detect_high_risk_tasks` | `probability >= 0.75` or `risk_level == HIGH` | `frequent_forgetting` |
| `detect_context_switching` | `switch_count >= 5` | `repeated_context_switching` |
| `detect_context_switching` | `interruption_time_minutes >= 15` | `high_interruption_cost` |
| `detect_context_switching` | `affected_category` present | `location_dependent_forgetting` |
| `detect_associations` | `confidence >= 0.7` and `lift >= 1.2` | `repeated_contextual_association` |
| `detect_friction_trend` | ≥2 `friction_score` metrics, least-squares slope sign | `increasing_friction` / `decreasing_friction` |

All thresholds are named module-level constants at the top of
`insight_engine.py` so they can be tuned without touching detection logic.

`detect_friction_trend` uses `app/analytics.py::compute_trend_slope`, a
deterministic least-squares fit (`numpy.polyfit`, degree 1) over the full
ordered `friction_score` series rather than comparing only the first and
last points. This is descriptive statistics computed over already-observed
values — not a forecast of future friction — so it stays within this
module's "no prediction" boundary. `app/analytics.py` also exposes
`summarize_metric_series()` (count/mean/min/max/slope via pandas/numpy) as a
reusable building block for any future metric-based insight.

Every `Insight` carries an `evidence: List[Evidence]` list. Each `Evidence`
item has a `field`, `value`, and `source` string that identifies exactly
which input object and field the value was read from. This is what makes the
"never invent statistics" requirement enforceable and testable — see
`tests/test_insight_engine.py::test_evidence_values_trace_to_input`.

## Ranking (`ranking.py`)

Insights are scored with a weighted sum of six normalized [0,1] signals:

```
rank_score = 0.30 * frequency
           + 0.25 * time_cost
           + 0.25 * risk_probability
           + 0.10 * repetition
           + 0.05 * recency
           + 0.05 * user_relevance
```

- **frequency**: scaled count evidence (e.g. `switch_count`,
  `previous_forgetting_count`), soft-capped at 10.
- **time_cost**: scaled `*_minutes` evidence, soft-capped at 60 minutes.
- **risk_probability**: the insight's `confidence` (an upstream
  probability/confidence value) when present, else a neutral 0.5.
- **repetition**: 1.0 if the same insight type recurs in the batch, else 0.0.
- **recency**: currently fixed at 1.0 (see docstring in `ranking.py` for why,
  and how to extend once historical insight timestamps exist).
- **user_relevance**: neutral 0.5, boosted to 1.0 when the upstream model
  already flagged `HIGH` priority. Documented hook for future
  personalization (e.g. per-user feedback history).

The resulting score is bucketed into `HIGH` (≥0.66) / `MEDIUM` (≥0.33) /
`LOW`, with one safety rule: an upstream-declared `HIGH` priority is never
silently downgraded below `MEDIUM`, since that already reflects a judgment
made by the source ML model.

## Recommendations (`recommendations.py`)

Built only from `Association` records with `confidence >= 0.5`, optionally
paired with a matching `ForgettingPrediction` for the same task (matched by
exact task name). If no matching prediction exists, `forgetting_probability`
is left `None` rather than guessed.

```
rank_score = 0.6 * association.confidence + 0.4 * (forgetting_probability or 0)
```

## Daily summary (`daily_summary.py`)

- `highest_risk_task` / `highest_risk_probability`: the single
  `ForgettingPrediction` with the maximum `probability`.
- `biggest_friction`: the title of the top-ranked insight (or "Context
  switching" if there are context insights but no ranked insight).
- `estimated_avoidable_friction_minutes`: sum of `recovery_cost_minutes`
  across all `ContextInsight` records.
- `context_reminder`: built from the highest-confidence `Association` with
  `confidence >= 0.7`.

All four fields degrade to `None` gracefully when their supporting input is
absent — see `tests/test_daily_summary.py::test_daily_summary_handles_empty_bundle`.
