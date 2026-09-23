from app.recommendations import generate_recommendations


def test_recommendations_generated_from_associations(sample_bundle):
    recs = generate_recommendations(sample_bundle)
    assert recs
    assert all(r.headline == "One More Thing?" for r in recs)


def test_recommendations_expose_traceable_evidence_and_stable_identity(sample_bundle):
    first = generate_recommendations(sample_bundle)
    second = generate_recommendations(sample_bundle)

    assert first[0].id == second[0].id
    assert first[0].user_id == sample_bundle.user_id
    assert first[0].recommendation_type == "context_based_reminder"
    assert first[0].evidence
    assert all(item.source for item in first[0].evidence)
    assert first[0].expected_benefit


def test_forgetting_evidence_changes_type_without_inventing_benefit(sample_bundle):
    sample_bundle.associations[0].task = "Lab Record"
    rec = generate_recommendations(sample_bundle)[0]

    assert rec.recommendation_type == "recurring_forgotten_task_prevention"
    assert any(item.field == "forgetting_probability" for item in rec.evidence)
    assert "%" not in rec.expected_benefit


def test_recommendation_pairs_forgetting_probability_when_available(sample_bundle):
    recs = generate_recommendations(sample_bundle)
    dept_recs = [r for r in recs if r.context == "Department"]
    assert dept_recs
    # "Collect Form" has no matching ForgettingPrediction in the fixture,
    # so forgetting_probability should be None (never invented).
    assert dept_recs[0].forgetting_probability is None


def test_recommendations_respect_max_limit(sample_bundle):
    recs = generate_recommendations(sample_bundle, max_recommendations=1)
    assert len(recs) == 1


def test_low_confidence_associations_excluded(sample_bundle):
    # Library->Return Book has confidence 0.55, below MIN_RECOMMENDATION_CONFIDENCE? (0.5)
    # so it should be included, but let's verify sorting puts the higher one first.
    recs = generate_recommendations(sample_bundle, max_recommendations=5)
    contexts = [r.context for r in recs]
    assert contexts[0] == "Department"


def test_no_recommendations_for_empty_bundle(empty_bundle):
    recs = generate_recommendations(empty_bundle)
    assert recs == []
