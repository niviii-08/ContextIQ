# ContextIQ Data Pipeline

## Objective

The pipeline converts timestamped behavioural records into reproducible sessions, metrics, historical features, and model-ready data without using information that would not have existed at prediction time.

## Event Semantics

| Event/data | Meaning |
|---|---|
| Task | A unit of work with category, priority, context, and lifecycle status |
| Task event | A lifecycle transition such as created, started, paused, resumed, completed, forgotten, or cancelled |
| Interruption | A time-bounded disruption associated with a task or session |
| Context/location | A user-defined environment or situational context |
| Session | A reconstructed interval of focused work, interruptions, and context switches |
| User | The ownership boundary for tasks, events, analytics, and recommendations |

## Processing Stages

1. **Validation**: Check required columns, types, timestamps, enumerations, and referential relationships.
2. **Cleaning**: Normalize timestamps, remove or flag malformed records, handle duplicates, and bound extreme values.
3. **Transformation**: Derive ordered event fields and analysis-ready timestamps.
4. **Session reconstruction**: Group event sequences by user/task and close dangling sessions defensively.
5. **Feature engineering**: Build one row per task using a strict `as_of = task.created_at` cutoff.
6. **ML export**: Write a temporal dataset and feature schema with completeness and range metadata.
7. **Training**: Compare candidate models and persist artifacts.
8. **Analytics population**: Produce user-scoped metrics and recommendations.
9. **Quality reporting**: Record row counts, null rates, sequence validity, and class balance.

The implementation is in `data-engine/pipeline/`; the orchestrator is `data-engine/pipeline/run_pipeline.py`.

## Leakage Contract

For a task at time `T.created_at`, historical slices use strict `< T.created_at` filters for task creation, event time, interruption start, and session start. The task's final status is used only as the label `will_forget`, never as an input feature. Chronological train/validation/test partitions ensure future rows cannot train a model evaluated on earlier behaviour.

## Data Quality Policy

- Missing required timestamps are rejected or reported before session reconstruction.
- Out-of-order events are sorted for deterministic processing and flagged for audit.
- Duplicate events should be removed using a stable event identifier or a documented natural-key rule.
- Empty inputs return empty, typed outputs rather than fabricated metrics.
- Numeric extremes are bounded or reported so a single malformed duration cannot dominate a metric.
- Unknown categories are rejected at strict API boundaries and handled as unknown/error values in batch validation according to the service contract.
- Schema changes require updates to the relevant Pydantic schemas, feature contract, tests, and documentation.

## Outputs

Typical outputs include session summaries, feature matrices, `feature_schema.json`, quality reports, model artifacts, and analytics API responses. Generated datasets and large artifacts are intentionally not treated as source documentation; regenerate them with the documented pipeline commands.

See the detailed [data-engine pipeline](../data-engine/docs/PIPELINE.md), [feature engine](../data-engine/docs/FEATURE_ENGINE.md), and [feature dictionary](FEATURE_DICTIONARY.md).
