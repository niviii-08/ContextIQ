# Association Mining ("One More Thing" — System B)

Covers transaction generation, Apriori/FP-Growth mining, metric
definitions, and the recommendation generator.

## 1. Transactions

`ml/associations/transactions.py::generate_transactions(events, session_gap_minutes=60)`

A **transaction** is the basket of distinct `task_id`s a user completed
during one continuous "visit" to a context. A visit is a maximal run of
`COMPLETE` events for the same `(user_id, context)` where consecutive
events are no more than `session_gap_minutes` apart (default 60). A
longer gap starts a new transaction.

Example — a single department visit:

```json
{
  "transaction_id": "…",
  "user_id": "user_001",
  "context": "department",
  "tasks": ["collect_form", "submit_record", "ask_faculty"]
}
```

Only `COMPLETE` events contribute — a task must have actually finished to
count as "occurring" in the visit. `transactions_to_basket_list(...)`
extracts the plain `list[list[str]]` basket format required by mlxtend.

## 2. Frequent itemset mining

`ml/associations/mining.py::mine_frequent_itemsets(baskets, algorithm, min_support)`

Wraps mlxtend's `apriori` and `fpgrowth`, both operating on a one-hot
encoded transaction matrix (`TransactionEncoder`). Both algorithms are
guaranteed to return the same frequent itemsets and support values for
the same input and `min_support` — they differ only in computational
strategy (candidate generation vs. FP-tree), which is why the module
exposes both behind one interface and lets the caller pick.

## 3. Metric definitions

Given a transaction database `D` of `N` transactions, and itemsets `A`
(antecedent) and `B` (consequent):

| metric | formula | meaning |
|---|---|---|
| `support(A)` | `count(transactions containing A) / N` | how common `A` is on its own |
| `support(A→B)` | `count(transactions containing A and B) / N` | how common the co-occurrence of `A` and `B` is |
| `confidence(A→B)` | `support(A→B) / support(A)` | given `A` occurred, how often `B` also occurred |
| `lift(A→B)` | `confidence(A→B) / support(B)` | how much more likely `B` is given `A`, vs. `B`'s baseline rate. `lift == 1`: independent. `lift > 1`: positive association. `lift < 1`: negative association. |

## 4. Rule mining and filtering

`ml/associations/mining.py::mine_association_rules(baskets, context, algorithm, min_support, min_confidence, min_lift, include_popularity_rules=True)`

1. Mines frequent itemsets via the chosen algorithm.
2. Derives candidate rules via mlxtend's `association_rules`, filtered by
   `min_confidence`.
3. Defensively re-applies `min_support` and `min_lift` thresholds (the
   "filter weak associations" requirement) — all three thresholds are
   configurable per call.
4. **Popularity rules**: also includes unconditional `context → task`
   rules derived from frequent 1-itemsets (`antecedents=[]`), so a task
   that is simply "frequently done during this context" (independent of
   any other completed task) is still a valid recommendation candidate —
   this is what lets `recommend_for_context` suggest something on a
   user's very first action in a visit, before any antecedent task has
   been completed. By construction, these rules have `confidence ==
   support` and `lift == 1.0` (exactly at the neutral/independence
   point), which still passes the default `min_lift=1.0` filter. Set
   `include_popularity_rules=False` to disable this and only get
   multi-item conditional rules.

Rules are returned sorted by `lift` desc, then `confidence` desc.

## 5. Recommendation generator

`ml/associations/recommender.py::recommend_for_context(user_id, context, rules, completed_tasks, config, dismissal_store, max_recommendations)`

Pipeline:

1. Filter `rules` to the given `context` and to those meeting
   `config.min_confidence / min_support / min_lift` (defensive re-check,
   since `rules` may come from any source, not only `mine_association_rules`).
2. Keep only rules whose antecedent tasks are a subset of
   `completed_tasks` (or whose antecedent is empty) — i.e. rules that are
   actually *applicable* to this visit's current state.
3. For each candidate consequent task, keep only its single best
   supporting rule (highest lift, then confidence) — de-duplication.
4. Drop tasks already in `completed_tasks`.
5. Drop tasks currently suppressed by `dismissal_store` (cooldown or
   explicit dismissal — see below).
6. Rank remaining recommendations by confidence desc, then lift desc,
   then support desc; truncate to `max_recommendations`.
7. Record each returned recommendation as "shown" in `dismissal_store`
   (starts its cooldown window) so the same suggestion isn't repeated on
   every request.

Nothing is hardcoded: every recommendation traces back to an
`AssociationRule` produced by mining real (or synthetic) transaction
data.

### Quality controls

`RecommendationQualityConfig`:

- `min_confidence` (default 0.5)
- `min_support` (default 0.05)
- `min_lift` (default 1.0)
- `cooldown_seconds` (default 3600) — how long a shown or dismissed
  recommendation is suppressed before it can be shown again.

`DismissalStore` is a minimal in-memory interface
(`record_dismissal`, `record_shown`, `is_suppressed`, `clear`) — swap for
a real persistence layer (e.g. a `dismissals` table keyed by
`(user_id, context, task)`) when integrating; the call sites do not need
to change.

## 6. Combined intelligence (optional)

`ml/associations/recommender.py::prioritize_recommendations(user_id, recommendations, forgetting_provider, association_weight=0.5, forgetting_weight=0.5)`

Blends each recommendation's association `confidence` with an external
**forgetting probability** into one `priority_score`:

```
priority_score = association_weight * confidence + forgetting_weight * forgetting_probability
```

If `forgetting_provider` is `None` (or returns `None` for a task), the
score falls back to `confidence` alone, so this pipeline works completely
standalone without the forgetting model existing.

`ForgettingRiskProvider` is the interface a real forgetting-risk model
must implement (`get_forgetting_probability(user_id, task) -> float |
None`). This module only ships `MockForgettingRiskProvider`, a
deterministic stand-in for tests/demos — the real model is a separate
module, as required.
