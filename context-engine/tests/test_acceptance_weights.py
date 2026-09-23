import pytest

from ml.associations.mining import (
    acceptance_rate_from_feedback,
    mine_association_rules,
)


def _synthetic_baskets() -> list[list[str]]:
    baskets = []
    for _ in range(40):
        baskets.append(["task_a", "task_b"])
    for _ in range(10):
        baskets.append(["task_a", "task_b", "task_c"])
    for _ in range(10):
        baskets.append(["task_a"])
    for _ in range(5):
        baskets.append(["task_d"])
    return baskets


def test_acceptance_rate_from_feedback():
    ant = ["task_a"]
    cons = ["task_b"]
    feedback_rows = []
    for _ in range(3):
        feedback_rows.append({"antecedent": ant, "consequent": cons, "action": "ACCEPTED"})
    for _ in range(1):
        feedback_rows.append({"antecedent": ant, "consequent": cons, "action": "DEFERRED"})

    weights = acceptance_rate_from_feedback(feedback_rows)
    key = (frozenset(ant), frozenset(cons))
    assert key in weights
    assert weights[key] == 5.0


def test_weighted_confidence_increases_with_feedback():
    baskets = _synthetic_baskets()
    ant = frozenset(["task_a"])
    cons = frozenset(["task_b"])

    rules_no_weights = mine_association_rules(
        baskets, context="ctx", min_support=0.1, min_confidence=0.5
    )
    target_no_weight = next(
        r
        for r in rules_no_weights
        if frozenset(r.antecedents) == ant and frozenset(r.consequents) == cons
    )
    C0 = target_no_weight.confidence

    explicit_weights = {(ant, cons): 5.0}
    rules_with_weights = mine_association_rules(
        baskets, context="ctx", min_support=0.1, min_confidence=0.5, acceptance_weights=explicit_weights
    )
    target_with_weight = next(
        r
        for r in rules_with_weights
        if frozenset(r.antecedents) == ant and frozenset(r.consequents) == cons
    )
    assert target_with_weight.weighted_confidence is not None
    assert target_with_weight.weighted_confidence > C0


def test_weight_cap_5x():
    baskets = _synthetic_baskets()
    ant = frozenset(["task_a"])
    cons = frozenset(["task_b"])

    rules_baseline = mine_association_rules(
        baskets, context="ctx", min_support=0.1, min_confidence=0.5
    )
    target_baseline = next(
        r
        for r in rules_baseline
        if frozenset(r.antecedents) == ant and frozenset(r.consequents) == cons
    )
    C0 = target_baseline.confidence

    explicit_weights = {(ant, cons): 10.0}
    rules_capped = mine_association_rules(
        baskets, context="ctx", min_support=0.1, min_confidence=0.5, acceptance_weights=explicit_weights
    )
    target_capped = next(
        r
        for r in rules_capped
        if frozenset(r.antecedents) == ant and frozenset(r.consequents) == cons
    )
    assert target_capped.weighted_confidence is not None
    assert target_capped.weighted_confidence <= 5.0 * C0
