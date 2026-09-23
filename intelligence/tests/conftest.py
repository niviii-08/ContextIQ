import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.schemas import (
    Association,
    BehaviourMetric,
    ContextInsight,
    ForgettingPrediction,
    IntelligenceBundle,
    RiskLevel,
)


@pytest.fixture
def sample_bundle() -> IntelligenceBundle:
    return IntelligenceBundle(
        user_id="user_123",
        forgetting_predictions=[
            ForgettingPrediction(
                task="Lab Record",
                probability=0.82,
                risk_level=RiskLevel.HIGH,
                model_version="forgetting-v2.3",
                contributing_features=["monday_pattern"],
                previous_forgetting_count=4,
                weekday_pattern="Monday",
            ),
            ForgettingPrediction(
                task="Submit Timesheet",
                probability=0.35,
                risk_level=RiskLevel.LOW,
                model_version="forgetting-v2.3",
                previous_forgetting_count=1,
            ),
        ],
        context_insights=[
            ContextInsight(
                switch_count=7,
                interruption_time_minutes=22.0,
                recovery_cost_minutes=18.0,
                top_interruption="Slack notifications",
                affected_category="Department tasks",
                period="2026-08-18",
            )
        ],
        associations=[
            Association(context="Department", task="Collect Form", support=0.4, confidence=0.78, lift=1.6),
            Association(context="Library", task="Return Book", support=0.2, confidence=0.55, lift=1.1),
        ],
        metrics=[
            BehaviourMetric(metric_name="friction_score", value=0.31, period="2026-08-11"),
            BehaviourMetric(metric_name="friction_score", value=0.44, period="2026-08-18"),
        ],
    )


@pytest.fixture
def empty_bundle() -> IntelligenceBundle:
    return IntelligenceBundle(user_id="user_empty")
