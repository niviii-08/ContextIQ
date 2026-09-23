"""
insight_engine.py
==================
Deterministic detection of behavioural patterns from structured ML outputs.

RULE: This module NEVER invents numbers. Every value placed into an Insight's
description or evidence must be read directly from the input schemas
(ForgettingPrediction, ContextInsight, Association, BehaviourMetric).

This module performs NO prediction, NO probability estimation, and NO
association mining. It only interprets already-computed structured results.
"""

from __future__ import annotations

from typing import List

from app.schemas import (
    Association,
    BehaviourMetric,
    ContextInsight,
    Evidence,
    ForgettingPrediction,
    Insight,
    InsightType,
    IntelligenceBundle,
    Priority,
    RiskLevel,
)

# ---------------------------------------------------------------------------
# Thresholds — deterministic, documented, tunable constants.
# These are business rules, not model outputs.
# ---------------------------------------------------------------------------

FREQUENT_FORGETTING_MIN_COUNT = 3
HIGH_SWITCH_COUNT_THRESHOLD = 5
HIGH_INTERRUPTION_MINUTES_THRESHOLD = 15.0
STRONG_ASSOCIATION_CONFIDENCE = 0.7
STRONG_ASSOCIATION_LIFT = 1.2
HIGH_RISK_PROBABILITY = 0.75


def _priority_for_probability(p: float) -> Priority:
    if p >= HIGH_RISK_PROBABILITY:
        return Priority.HIGH
    if p >= 0.5:
        return Priority.MEDIUM
    return Priority.LOW


def detect_frequent_forgetting(predictions: List[ForgettingPrediction]) -> List[Insight]:
    """Flag tasks with a documented history of repeated forgetting."""
    insights: List[Insight] = []
    for pred in predictions:
        if pred.previous_forgetting_count is not None and (
            pred.previous_forgetting_count >= FREQUENT_FORGETTING_MIN_COUNT
        ):
            evidence = [
                Evidence(
                    field="previous_forgetting_count",
                    value=str(pred.previous_forgetting_count),
                    source=f"ForgettingPrediction:{pred.task}",
                ),
                Evidence(
                    field="probability",
                    value=f"{pred.probability:.2f}",
                    source=f"ForgettingPrediction:{pred.task}",
                ),
            ]
            if pred.weekday_pattern:
                evidence.append(
                    Evidence(
                        field="weekday_pattern",
                        value=pred.weekday_pattern,
                        source=f"ForgettingPrediction:{pred.task}",
                    )
                )
            insights.append(
                Insight(
                    type=InsightType.FREQUENT_FORGETTING,
                    title=f"Frequent forgetting: {pred.task}",
                    description=(
                        f"'{pred.task}' has been forgotten "
                        f"{pred.previous_forgetting_count} times previously, "
                        f"with a current predicted forgetting probability of "
                        f"{pred.probability:.0%}."
                    ),
                    evidence=evidence,
                    priority=_priority_for_probability(pred.probability),
                    confidence=pred.probability,
                    source="forgetting_prediction",
                )
            )
    return insights


def detect_high_risk_tasks(predictions: List[ForgettingPrediction]) -> List[Insight]:
    """Flag any task whose forgetting probability alone crosses the high-risk bar,
    independent of forgetting history."""
    insights: List[Insight] = []
    for pred in predictions:
        if pred.probability >= HIGH_RISK_PROBABILITY or pred.risk_level == RiskLevel.HIGH:
            insights.append(
                Insight(
                    type=InsightType.FREQUENT_FORGETTING,
                    title=f"High forgetting risk: {pred.task}",
                    description=(
                        f"'{pred.task}' carries a {pred.probability:.0%} predicted "
                        f"forgetting risk (risk level: {pred.risk_level.value})."
                    ),
                    evidence=[
                        Evidence(
                            field="probability",
                            value=f"{pred.probability:.2f}",
                            source=f"ForgettingPrediction:{pred.task}",
                        ),
                        Evidence(
                            field="risk_level",
                            value=pred.risk_level.value,
                            source=f"ForgettingPrediction:{pred.task}",
                        ),
                    ],
                    priority=Priority.HIGH,
                    confidence=pred.probability,
                    source="forgetting_prediction",
                )
            )
    return insights


def detect_context_switching(context_insights: List[ContextInsight]) -> List[Insight]:
    """Flag repeated context switching and high interruption cost."""
    insights: List[Insight] = []
    for ci in context_insights:
        if ci.switch_count >= HIGH_SWITCH_COUNT_THRESHOLD:
            evidence = [
                Evidence(field="switch_count", value=str(ci.switch_count), source="ContextInsight"),
                Evidence(
                    field="recovery_cost_minutes",
                    value=f"{ci.recovery_cost_minutes:.1f}",
                    source="ContextInsight",
                ),
            ]
            description = (
                f"{ci.switch_count} context switches were recorded"
                + (f" during {ci.period}" if ci.period else "")
                + f", costing an estimated {ci.recovery_cost_minutes:.0f} minutes of recovery time."
            )
            insights.append(
                Insight(
                    type=InsightType.REPEATED_CONTEXT_SWITCHING,
                    title="Repeated context switching",
                    description=description,
                    evidence=evidence,
                    priority=Priority.HIGH if ci.switch_count >= HIGH_SWITCH_COUNT_THRESHOLD * 2 else Priority.MEDIUM,
                    source="context_switch_analysis",
                )
            )

        if ci.interruption_time_minutes >= HIGH_INTERRUPTION_MINUTES_THRESHOLD:
            evidence = [
                Evidence(
                    field="interruption_time_minutes",
                    value=f"{ci.interruption_time_minutes:.1f}",
                    source="ContextInsight",
                )
            ]
            desc = f"Interruptions consumed {ci.interruption_time_minutes:.0f} minutes"
            if ci.top_interruption:
                evidence.append(
                    Evidence(field="top_interruption", value=ci.top_interruption, source="ContextInsight")
                )
                desc += f", most frequently caused by '{ci.top_interruption}'"
            desc += "."
            insights.append(
                Insight(
                    type=InsightType.HIGH_INTERRUPTION_COST,
                    title="High interruption cost",
                    description=desc,
                    evidence=evidence,
                    priority=Priority.HIGH,
                    source="context_switch_analysis",
                )
            )

        if ci.affected_category:
            insights.append(
                Insight(
                    type=InsightType.LOCATION_DEPENDENT_FORGETTING,
                    title=f"Category-linked friction: {ci.affected_category}",
                    description=(
                        f"Friction was concentrated in the '{ci.affected_category}' category "
                        + (f"during {ci.period}." if ci.period else ".")
                    ),
                    evidence=[
                        Evidence(field="affected_category", value=ci.affected_category, source="ContextInsight")
                    ],
                    priority=Priority.MEDIUM,
                    source="context_switch_analysis",
                )
            )
    return insights


def detect_associations(associations: List[Association]) -> List[Insight]:
    """Flag strong, repeated contextual task associations."""
    insights: List[Insight] = []
    for assoc in associations:
        if assoc.confidence >= STRONG_ASSOCIATION_CONFIDENCE and assoc.lift >= STRONG_ASSOCIATION_LIFT:
            insights.append(
                Insight(
                    type=InsightType.REPEATED_CONTEXTUAL_ASSOCIATION,
                    title=f"Strong association: {assoc.context} → {assoc.task}",
                    description=(
                        f"When in context '{assoc.context}', task '{assoc.task}' is completed "
                        f"with {assoc.confidence:.0%} confidence (lift {assoc.lift:.2f}, "
                        f"support {assoc.support:.0%})."
                    ),
                    evidence=[
                        Evidence(field="confidence", value=f"{assoc.confidence:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
                        Evidence(field="lift", value=f"{assoc.lift:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
                        Evidence(field="support", value=f"{assoc.support:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
                    ],
                    priority=Priority.MEDIUM,
                    confidence=assoc.confidence,
                    source="association_mining",
                )
            )
    return insights


def detect_friction_trend(metrics: List[BehaviourMetric] = None, **kwargs) -> List[Insight]:
    """Detect increasing/decreasing friction from a 'friction_score' style metric
    when at least two comparable periods are present.

    Uses a deterministic least-squares slope (app.analytics.compute_trend_slope,
    numpy.polyfit degree-1) over the full ordered series rather than just the
    first/last points, so a single noisy period doesn't flip the verdict.
    This is descriptive statistics over already-observed values, not a
    forecast of future friction.
    """
    from app.analytics import compute_trend_slope  # local import avoids a hard cycle at module load

    metrics = metrics or []
    friction_metrics = [m for m in metrics if m.metric_name == "friction_score"]
    if len(friction_metrics) < 2:
        return []

    first, last = friction_metrics[0], friction_metrics[-1]
    values = [m.value for m in friction_metrics]
    slope = compute_trend_slope(values)

    insights: List[Insight] = []
    if slope is None or slope == 0:
        return insights

    evidence = [
        Evidence(field="value", value=f"{first.value:.2f}", source=f"BehaviourMetric:friction_score:{first.period}"),
        Evidence(field="value", value=f"{last.value:.2f}", source=f"BehaviourMetric:friction_score:{last.period}"),
        Evidence(field="slope", value=f"{slope:.4f}", source="BehaviourMetric:friction_score:trend"),
    ]

    if slope > 0:
        insights.append(
            Insight(
                type=InsightType.INCREASING_FRICTION,
                title="Friction is increasing",
                description=(
                    f"Friction score rose from {first.value:.2f} ({first.period}) to "
                    f"{last.value:.2f} ({last.period}), a least-squares trend slope of "
                    f"{slope:.4f} per period across {len(friction_metrics)} data points."
                ),
                evidence=evidence,
                priority=Priority.MEDIUM,
                source="behaviour_metrics",
            )
        )
    else:
        insights.append(
            Insight(
                type=InsightType.DECREASING_FRICTION,
                title="Friction is decreasing",
                description=(
                    f"Friction score fell from {first.value:.2f} ({first.period}) to "
                    f"{last.value:.2f} ({last.period}), a least-squares trend slope of "
                    f"{slope:.4f} per period across {len(friction_metrics)} data points."
                ),
                evidence=evidence,
                priority=Priority.LOW,
                source="behaviour_metrics",
            )
        )
    return insights


def generate_insights(bundle: IntelligenceBundle) -> List[Insight]:
    """Main entry point: run all deterministic detectors over a bundle."""
    insights: List[Insight] = []
    insights += detect_frequent_forgetting(bundle.forgetting_predictions)
    insights += detect_high_risk_tasks(bundle.forgetting_predictions)
    insights += detect_context_switching(bundle.context_insights)
    insights += detect_associations(bundle.associations)
    insights += detect_friction_trend(bundle.metrics)
    return insights
