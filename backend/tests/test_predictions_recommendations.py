import pytest
from app.services.routine_service import polish_and_bulletize_routine


def test_polish_routine_broken_english():
    raw = "wake up 7am eating break fast then going college then evening study 2hr sleep 10"
    polished = polish_and_bulletize_routine(raw)
    assert polished is not None
    assert "•" in polished
    assert "Wake up" in polished
    assert "college" in polished.lower()


def test_polish_routine_already_bulleted():
    raw = "• 7:00 AM – Wake up\n• 8:00 AM – Breakfast\n• 9:00 AM – Deep focus"
    polished = polish_and_bulletize_routine(raw)
    assert polished is not None
    assert polished.count("•") == 3


def test_polish_routine_empty():
    assert polish_and_bulletize_routine("") == ""
    assert polish_and_bulletize_routine(None) is None


def test_prediction_reasons_structure():
    reasons = [
        {"feature": "Cognitive Anchor", "impact": 0.42, "description": "High forgetting risk"},
        {"feature": "Ebbinghaus Decay", "impact": 0.28, "description": "Memory decay over time"},
    ]
    assert len(reasons) == 2
    assert reasons[0]["feature"] == "Cognitive Anchor"
    assert reasons[0]["impact"] > 0
