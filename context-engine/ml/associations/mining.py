"""
Association rule mining over context transactions.

Implements both Apriori and FP-Growth (via mlxtend), computing support,
confidence, and lift for each rule, and filtering weak associations
according to configurable thresholds.

Metric definitions
-------------------
Given a transaction database D of N transactions, and itemsets A
(antecedent) and B (consequent):

- support(A) = count(transactions containing A) / N
  "How common is A on its own."

- support(A -> B) = count(transactions containing A and B) / N
  "How common is the co-occurrence of A and B."

- confidence(A -> B) = support(A -> B) / support(A)
  "Given A occurred, how often did B also occur."

- lift(A -> B) = confidence(A -> B) / support(B)
  "How much more likely B is, given A, compared to B's baseline rate.
   lift == 1 means A and B are independent; lift > 1 means positive
   association; lift < 1 means negative association."
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

import pandas as pd

mlxtend_installed = True

try:
    from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
    from mlxtend.preprocessing import TransactionEncoder
except ModuleNotFoundError:
    mlxtend_installed = False

    def apriori(*args, **kwargs):
        raise RuntimeError(
            "mlxtend is not installed. pip install mlxtend to enable association rule mining."
        )

    def fpgrowth(*args, **kwargs):
        raise RuntimeError(
            "mlxtend is not installed. pip install mlxtend to enable association rule mining."
        )

    def association_rules(*args, **kwargs):
        raise RuntimeError(
            "mlxtend is not installed. pip install mlxtend to enable association rule mining."
        )

    class TransactionEncoder:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "mlxtend is not installed. pip install mlxtend to enable association rule mining."
            )

from app.schemas.associations import AssociationRule


def _encode_transactions(baskets: list[list[str]]) -> pd.DataFrame:
    te = TransactionEncoder()
    te_array = te.fit(baskets).transform(baskets)
    return pd.DataFrame(te_array, columns=te.columns_)


def mine_frequent_itemsets(
    baskets: list[list[str]],
    algorithm: Literal["apriori", "fpgrowth"] = "apriori",
    min_support: float = 0.1,
) -> pd.DataFrame:
    if not baskets:
        return pd.DataFrame(columns=["support", "itemsets"])

    encoded = _encode_transactions(baskets)
    if algorithm == "apriori":
        itemsets = apriori(encoded, min_support=min_support, use_colnames=True)
    elif algorithm == "fpgrowth":
        itemsets = fpgrowth(encoded, min_support=min_support, use_colnames=True)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return itemsets


def _popularity_rules(
    itemsets: "pd.DataFrame",
    context: str,
    min_support: float,
    min_confidence: float,
    min_lift: float,
    acceptance_weights: dict[tuple[frozenset[str], frozenset[str]], float] | None = None,
) -> list[AssociationRule]:
    """Build unconditional 'context -> task' rules from frequent 1-itemsets.

    These have an empty antecedent: they say "this task is frequently
    completed during a visit to this context at all", independent of any
    other task having already been completed. This is what lets
    `recommend_for_context` suggest a first "one more thing" even before
    the user has completed anything else in the current visit — matching
    the contract example where a recommendation is returned with only a
    context, not a completed-task antecedent.

    By definition, confidence == support here (nothing is being
    conditioned on) and lift == 1.0 (an item's rate given "no information"
    is just its own rate). These still pass the default min_lift=1.0
    threshold since lift is exactly 1.0, not below it.
    """
    acceptance_weights = acceptance_weights or {}
    rules: list[AssociationRule] = []
    singles = itemsets[itemsets["itemsets"].apply(lambda s: len(s) == 1)]
    for _, row in singles.iterrows():
        support = float(row["support"])
        if support < min_support or support < min_confidence:
            continue
        if 1.0 < min_lift:
            continue
        task = next(iter(row["itemsets"]))
        raw_confidence = round(support, 4)
        antecedent_fs = frozenset()
        consequent_fs = frozenset([task])
        weight = acceptance_weights.get((antecedent_fs, consequent_fs), 1.0)
        clamped_weight = min(max(weight, 1.0), 5.0)
        weighted_confidence = round(raw_confidence * clamped_weight, 4)
        rules.append(
            AssociationRule(
                context=context,
                antecedents=[],
                consequents=[task],
                support=round(support, 4),
                confidence=raw_confidence,
                weighted_confidence=weighted_confidence,
                lift=1.0,
            )
        )
    return rules


def mine_association_rules(
    baskets: list[list[str]],
    context: str,
    algorithm: Literal["apriori", "fpgrowth"] = "apriori",
    min_support: float = 0.1,
    min_confidence: float = 0.5,
    min_lift: float = 1.0,
    include_popularity_rules: bool = True,
    acceptance_weights: dict[tuple[frozenset[str], frozenset[str]], float] | None = None,
) -> list[AssociationRule]:
    """Mine association rules from a list of task baskets for one context.

    Returns rules filtered to meet all three thresholds simultaneously
    (support, confidence, lift), which is the "filter weak associations"
    requirement. When `include_popularity_rules` is True (default), also
    includes unconditional context->task rules derived from frequent
    1-itemsets (see `_popularity_rules`), so a fresh visit with nothing
    completed yet still has "one more thing" candidates.

    The optional `acceptance_weights` parameter maps (antecedent, consequent)
    frozenset pairs to a weight multiplier. Each rule's `weighted_confidence`
    is computed as raw_confidence * clamp(weight, 1.0, 5.0), allowing
    user feedback to boost (but never lower) a rule's effective ranking
    score within the [1x, 5x] range.
    """
    acceptance_weights = acceptance_weights or {}
    itemsets = mine_frequent_itemsets(baskets, algorithm=algorithm, min_support=min_support)
    if itemsets.empty:
        return []

    popularity_rules = (
        _popularity_rules(itemsets, context, min_support, min_confidence, min_lift, acceptance_weights)
        if include_popularity_rules
        else []
    )

    try:
        rules_df = association_rules(
            itemsets, metric="confidence", min_threshold=min_confidence, num_itemsets=len(baskets)
        )
    except TypeError:
        # Older mlxtend versions do not require num_itemsets.
        rules_df = association_rules(itemsets, metric="confidence", min_threshold=min_confidence)

    if rules_df.empty:
        popularity_rules.sort(key=lambda r: (r.confidence, r.support), reverse=True)
        return popularity_rules

    rules_df = rules_df[rules_df["lift"] >= min_lift]
    rules_df = rules_df[rules_df["support"] >= min_support]

    rules: list[AssociationRule] = list(popularity_rules)
    for _, row in rules_df.iterrows():
        antecedent_list = sorted(list(row["antecedents"]))
        consequent_list = sorted(list(row["consequents"]))
        antecedent_fs = frozenset(antecedent_list)
        consequent_fs = frozenset(consequent_list)
        raw_confidence = round(float(row["confidence"]), 4)
        weight = acceptance_weights.get((antecedent_fs, consequent_fs), 1.0)
        clamped_weight = min(max(weight, 1.0), 5.0)
        weighted_confidence = round(raw_confidence * clamped_weight, 4)
        rules.append(
            AssociationRule(
                context=context,
                antecedents=antecedent_list,
                consequents=consequent_list,
                support=round(float(row["support"]), 4),
                confidence=raw_confidence,
                weighted_confidence=weighted_confidence,
                lift=round(float(row["lift"]), 4),
                leverage=round(float(row["leverage"]), 4) if "leverage" in row else None,
                conviction=(
                    round(float(row["conviction"]), 4)
                    if "conviction" in row and pd.notna(row["conviction"]) and row["conviction"] != float("inf")
                    else None
                ),
            )
        )

    # Sort by lift desc, then confidence desc — most actionable rules first.
    rules.sort(key=lambda r: (r.lift, r.confidence), reverse=True)
    return rules


def acceptance_rate_from_feedback(
    feedback_rows: list[dict],
) -> dict[tuple[frozenset[str], frozenset[str]], float]:
    """Compute acceptance-rate weights from feedback rows.

    Each row is expected to have keys:
      - antecedent: list[str]
      - consequent: list[str]
      - action: "ACCEPTED" | "DISMISSED" | "DEFERRED"

    Rows are grouped by (frozenset(antecedent), frozenset(consequent)).
    For each group:
      acceptance_rate = accepted / (accepted + dismissed)  (deferred excluded)
      weight = 1.0 + 4.0 * acceptance_rate  =>  1x at 0%, 5x at 100%

    Returns a mapping suitable for the `acceptance_weights` argument of
    `mine_association_rules`.
    """
    grouped: dict[tuple[frozenset[str], frozenset[str]], dict[str, int]] = defaultdict(
        lambda: {"accepted": 0, "dismissed": 0, "deferred": 0}
    )
    for row in feedback_rows:
        ant = frozenset(row["antecedent"])
        cons = frozenset(row["consequent"])
        key = (ant, cons)
        action = row["action"].upper()
        if action == "ACCEPTED":
            grouped[key]["accepted"] += 1
        elif action == "DISMISSED":
            grouped[key]["dismissed"] += 1
        elif action == "DEFERRED":
            grouped[key]["deferred"] += 1

    weights: dict[tuple[frozenset[str], frozenset[str]], float] = {}
    for key, counts in grouped.items():
        accepted = counts["accepted"]
        dismissed = counts["dismissed"]
        non_deferred = accepted + dismissed
        acceptance_rate = accepted / non_deferred if non_deferred > 0 else 0.0
        weights[key] = 1.0 + 4.0 * acceptance_rate
    return weights
