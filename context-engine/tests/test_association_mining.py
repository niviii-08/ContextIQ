from ml.associations.mining import mine_association_rules, mine_frequent_itemsets


def _department_baskets():
    # Strong association: collect_form + submit_record co-occur often;
    # ask_faculty appears less often; pay_fee is rare/noise.
    baskets = []
    for _ in range(30):
        baskets.append(["collect_form", "submit_record"])
    for _ in range(10):
        baskets.append(["collect_form", "submit_record", "ask_faculty"])
    for _ in range(5):
        baskets.append(["collect_form"])
    for _ in range(2):
        baskets.append(["pay_fee"])
    return baskets


def test_apriori_and_fpgrowth_find_frequent_itemsets():
    baskets = _department_baskets()
    apriori_sets = mine_frequent_itemsets(baskets, algorithm="apriori", min_support=0.1)
    fpgrowth_sets = mine_frequent_itemsets(baskets, algorithm="fpgrowth", min_support=0.1)
    assert not apriori_sets.empty
    assert not fpgrowth_sets.empty
    # Same support values regardless of algorithm.
    assert set(round(x, 4) for x in apriori_sets["support"]) == set(
        round(x, 4) for x in fpgrowth_sets["support"]
    )


def test_rules_meet_thresholds():
    baskets = _department_baskets()
    rules = mine_association_rules(
        baskets, context="department", algorithm="apriori", min_support=0.1, min_confidence=0.5, min_lift=1.0
    )
    assert len(rules) > 0
    for r in rules:
        assert r.support >= 0.1
        assert r.confidence >= 0.5
        assert r.lift >= 1.0
        assert r.context == "department"


def test_strong_pair_appears_in_rules():
    baskets = _department_baskets()
    rules = mine_association_rules(
        baskets, context="department", algorithm="apriori", min_support=0.1, min_confidence=0.5, min_lift=1.0
    )
    found = any(
        set(r.antecedents) == {"collect_form"} and set(r.consequents) == {"submit_record"} for r in rules
    )
    assert found


def test_empty_baskets_returns_no_rules():
    rules = mine_association_rules([], context="department")
    assert rules == []


def test_weak_associations_filtered_out():
    baskets = _department_baskets()
    # High confidence threshold should filter out weak rules involving pay_fee.
    rules = mine_association_rules(
        baskets, context="department", algorithm="apriori", min_support=0.3, min_confidence=0.8, min_lift=1.0
    )
    for r in rules:
        assert "pay_fee" not in r.antecedents
        assert "pay_fee" not in r.consequents
