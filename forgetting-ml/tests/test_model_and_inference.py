import pytest

from app.inference import ForgettingPredictor


@pytest.fixture(scope="module")
def predictor():
    return ForgettingPredictor.instance()


def test_model_loads(predictor):
    assert predictor.model is not None
    assert predictor.model_version is not None
    assert predictor.model_name in ("logistic_regression", "random_forest", "xgboost")


def test_single_prediction_shape(predictor, sample_task_payload):
    result = predictor.predict_single(sample_task_payload)
    assert "prediction_probability" in result
    assert "risk_level" in result
    assert "model_version" in result
    assert "top_features" in result
    assert isinstance(result["top_features"], list)
    assert len(result["top_features"]) > 0


def test_probability_in_valid_range(predictor, sample_task_payload):
    result = predictor.predict_single(sample_task_payload)
    prob = result["prediction_probability"]
    assert 0.0 <= prob <= 1.0


def test_risk_level_matches_probability(predictor, sample_task_payload):
    result = predictor.predict_single(sample_task_payload)
    prob = result["prediction_probability"]
    risk = result["risk_level"]
    if prob < 0.33:
        assert risk == "LOW"
    elif prob < 0.66:
        assert risk == "MEDIUM"
    else:
        assert risk == "HIGH"


def test_batch_prediction_matches_single(predictor, sample_task_payload):
    single = predictor.predict_single(sample_task_payload)
    batch = predictor.predict_batch([sample_task_payload, sample_task_payload])
    assert len(batch) == 2
    assert batch[0]["prediction_probability"] == single["prediction_probability"]
    assert batch[0]["prediction_probability"] == batch[1]["prediction_probability"]


def test_batch_prediction_empty_list(predictor):
    assert predictor.predict_batch([]) == []


def test_missing_feature_raises(predictor, sample_task_payload):
    bad_payload = dict(sample_task_payload)
    del bad_payload["historical_completion_rate"]
    with pytest.raises(ValueError):
        predictor.predict_batch([bad_payload])


def test_different_inputs_can_yield_different_predictions(predictor, sample_task_payload):
    low_risk_payload = dict(sample_task_payload)
    low_risk_payload.update({
        "historical_completion_rate": 0.95,
        "historical_forgetting_rate": 0.02,
        "previous_forgetting_count": 0,
        "interruptions_today": 0,
        "recent_context_switches": 0,
    })
    high_risk_payload = dict(sample_task_payload)
    high_risk_payload.update({
        "historical_completion_rate": 0.05,
        "historical_forgetting_rate": 0.9,
        "previous_forgetting_count": 40,
        "interruptions_today": 15,
        "recent_context_switches": 15,
    })
    low = predictor.predict_single(low_risk_payload)
    high = predictor.predict_single(high_risk_payload)
    # Not guaranteed to be strictly monotonic for every combination, but for
    # these two clearly-separated feature sets, model output should differ.
    assert low["prediction_probability"] != high["prediction_probability"]
