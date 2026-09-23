# Evaluation

Offline evaluation helpers live in `ml/evaluation/evaluate.py` and are
meant to be run from `scripts/run_pipeline.py`, a notebook, or a
dedicated evaluation script — they are not part of the live API request
path.

## Session / pattern quality

`session_summary_report(sessions)` flattens reconstructed sessions into a
`pandas.DataFrame` for quick inspection, plotting, or export (see
`artifacts/session_summary.csv` after running `scripts/run_pipeline.py`).

There is no single "ground truth" for behavioural-pattern discovery
(clustering/anomaly detection are unsupervised), so evaluation here is
necessarily qualitative:

- Inspect `discover_frequency_patterns` output against known synthetic
  biases (the synthetic generator gives each user a preferred context, so
  frequency patterns should surface a plausible signal there).
- Inspect cluster centroids from `discover_clusters` for sensible,
  human-interpretable separation (e.g. one cluster should have visibly
  higher `interruption_time_seconds` than another).
- Spot-check anomalies from `discover_anomalies` — they should correspond
  to sessions with genuinely unusual timing profiles (extreme
  interruption counts, extreme durations, etc.), not arbitrary noise.

## Recovery cost sanity checks

Recovery cost has no ground truth by design (see
`docs/CONTEXT_INTELLIGENCE.md`, section 5). The only property to test for
is **monotonicity**: sessions with strictly more/longer interruptions and
switches should score at or above sessions with fewer/shorter ones, all
else equal. `tests/test_recovery_cost.py::test_recovery_cost_ranks_worse_session_higher`
checks exactly this.

## Association rule quality

`rule_quality_report(rules)` flattens mined rules into a `DataFrame`
sorted by lift then confidence, for inspection or export (see
`artifacts/association_rules.csv`).

Beyond eyeballing, two standard offline recommender metrics are provided:

- `precision_at_k(recommended, relevant, k)` — of the top-`k` recommended
  tasks, what fraction were actually completed by the user (from a
  held-out portion of their history)?
- `recall_at_k(recommended, relevant, k)` — of all tasks the user
  actually completed (held out), what fraction appeared in the top-`k`
  recommendations?

### Suggested offline evaluation procedure

1. Split each user's transactions chronologically: mine rules on the
   earlier 80% of their visits to a context, hold out the later 20%.
2. For each held-out visit, reveal tasks one at a time (simulating
   `completed_tasks` growing), call `recommend_for_context`, and record
   whether the next actually-completed task appeared in the
   recommendation list.
3. Aggregate `precision_at_k` / `recall_at_k` across held-out visits.

This procedure is intentionally not wired into a script here (it depends
on how ContextIQ wants to define "held out" per user in production data)
— the building blocks (`precision_at_k`, `recall_at_k`,
`rule_quality_report`) are provided so the integrating team can assemble
it against real data.

## Running the demo pipeline

```bash
python scripts/generate_synthetic_data.py
python scripts/run_pipeline.py
```

This prints System A metrics/patterns/recovery-cost summaries and System
B transaction/rule counts to stdout, and writes:

- `artifacts/session_summary.csv`
- `artifacts/association_rules.csv`
- `artifacts/focused_vs_interruption.png`

## Running the test suite

```bash
pytest -q
```

46 tests cover session reconstruction, context-switch metrics, recovery
cost estimation, transaction generation, Apriori, FP-Growth,
support/confidence/lift correctness, recommendation filtering
(thresholds, de-duplication, antecedent applicability), cooldown,
dismissal support, the mock forgetting-risk integration, and all four API
endpoints.
