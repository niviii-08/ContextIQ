"""
Experimental Behavioural Friction Score
=========================================

**Experimental behavioural metric — not scientifically validated.**

This score is a transparent, heuristic composite intended to give a
single at-a-glance number for "how much behavioural friction is this
person experiencing right now". It is NOT a clinically or scientifically
validated instrument — it is a deliberately simple, explainable formula
so it can be inspected, criticised, and iterated on.

COMPONENTS (each normalized to a 0-100 scale, higher = worse friction)
------------------------------------------------------------------------
1. forgetting_score
   = 100 * task_forgetting_rate
   Directly proportional to the fraction of resolved tasks that were
   forgotten (i.e. task_forgetting_rate 0.0-1.0 -> 0-100).

2. interruption_score
   = 100 * min(1, interruptions_per_active_hour / INTERRUPTION_SATURATION)
   Where `interruptions_per_active_hour` = total interruptions /
   (total focused+interruption time across sessions, in hours).
   INTERRUPTION_SATURATION (default 6/hr) is the rate considered "maximum
   observed friction" for normalization purposes — beyond that the score
   saturates at 100 rather than growing unbounded.

3. context_switch_score
   = 100 * min(1, context_switches_per_session / SWITCH_SATURATION)
   SWITCH_SATURATION (default 3 switches/session) is the normalization
   ceiling.

4. recovery_score
   = 100 * min(1, average_resume_delay_minutes / RECOVERY_SATURATION_MINUTES)
   RECOVERY_SATURATION_MINUTES (default 30 minutes) — the average time it
   takes a user to resume a paused task, normalized against a half-hour
   ceiling.

OVERALL SCORE
-------------
overall_score = weighted average of the four components:
    0.35 * forgetting_score
  + 0.25 * interruption_score
  + 0.20 * context_switch_score
  + 0.20 * recovery_score

Weights reflect an assumption (not empirically derived) that forgetting
entire tasks is the costliest friction, interruptions are the next most
costly, and context-switch frequency / slow recovery are somewhat less
costly but still meaningful. These weights are configurable constants
below and should be tuned once real usage data is available.

All sub-scores and the overall score are clamped to [0, 100].
"""
from __future__ import annotations

INTERRUPTION_SATURATION_PER_HOUR = 6.0
SWITCH_SATURATION_PER_SESSION = 3.0
RECOVERY_SATURATION_MINUTES = 30.0

WEIGHT_FORGETTING = 0.35
WEIGHT_INTERRUPTION = 0.25
WEIGHT_CONTEXT_SWITCH = 0.20
WEIGHT_RECOVERY = 0.20


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def compute_forgetting_score(task_forgetting_rate: float) -> float:
    return _clamp(100.0 * task_forgetting_rate)


def compute_interruption_score(interruption_count: int, total_active_seconds: float) -> float:
    if total_active_seconds <= 0:
        return 0.0
    active_hours = total_active_seconds / 3600.0
    if active_hours <= 0:
        return 0.0
    rate_per_hour = interruption_count / active_hours
    ratio = rate_per_hour / INTERRUPTION_SATURATION_PER_HOUR
    return _clamp(100.0 * min(1.0, ratio))


def compute_context_switch_score(total_context_switches: int, total_sessions: int) -> float:
    if total_sessions <= 0:
        return 0.0
    switches_per_session = total_context_switches / total_sessions
    ratio = switches_per_session / SWITCH_SATURATION_PER_SESSION
    return _clamp(100.0 * min(1.0, ratio))


def compute_recovery_score(average_resume_delay_seconds: float | None) -> float:
    if average_resume_delay_seconds is None:
        return 0.0
    minutes = average_resume_delay_seconds / 60.0
    ratio = minutes / RECOVERY_SATURATION_MINUTES
    return _clamp(100.0 * min(1.0, ratio))


def compute_overall_score(
    forgetting_score: float,
    interruption_score: float,
    context_switch_score: float,
    recovery_score: float,
) -> float:
    overall = (
        WEIGHT_FORGETTING * forgetting_score
        + WEIGHT_INTERRUPTION * interruption_score
        + WEIGHT_CONTEXT_SWITCH * context_switch_score
        + WEIGHT_RECOVERY * recovery_score
    )
    return round(_clamp(overall), 2)


def compute_friction_score(
    *,
    task_forgetting_rate: float,
    interruption_count: int,
    total_active_seconds: float,
    total_context_switches: int,
    total_sessions: int,
    average_resume_delay_seconds: float | None,
) -> dict:
    forgetting = compute_forgetting_score(task_forgetting_rate)
    interruption = compute_interruption_score(interruption_count, total_active_seconds)
    context_switch = compute_context_switch_score(total_context_switches, total_sessions)
    recovery = compute_recovery_score(average_resume_delay_seconds)
    overall = compute_overall_score(forgetting, interruption, context_switch, recovery)

    return {
        "overall_score": overall,
        "forgetting_score": round(forgetting, 2),
        "interruption_score": round(interruption, 2),
        "context_switch_score": round(context_switch, 2),
        "recovery_score": round(recovery, 2),
    }
