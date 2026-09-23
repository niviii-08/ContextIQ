"""
Behavioural pattern discovery over reconstructed sessions.

Implements three complementary, classical (non-deep-learning) techniques:

1. Frequency analysis
   - Finds (task_category, context) pairs with disproportionately high
     interruption or switch rates using simple contingency-style ratios.

2. Clustering (KMeans over engineered session features)
   - Groups sessions into behavioural clusters (e.g. "high-switch/low-focus"
     vs "low-switch/high-focus") and describes each cluster's centroid.

3. Anomaly detection (IsolationForest over the same feature space)
   - Flags sessions whose timing profile is unusual relative to the rest
     of the user's (or population's) sessions.

All techniques operate on transparent, hand-engineered features derived
directly from `ReconstructedSession` fields — no raw text/NLP, no deep
learning, consistent with the "do not use deep learning unnecessarily"
requirement.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.schemas.context import ReconstructedSession, BehaviouralPattern


def _sessions_to_frame(sessions: list[ReconstructedSession]) -> pd.DataFrame:
    rows = []
    for s in sessions:
        rows.append(
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "task_category": s.task_category,
                "context": s.context,
                "session_duration_seconds": s.session_duration_seconds,
                "focused_time_seconds": s.focused_time_seconds,
                "interruption_time_seconds": s.interruption_time_seconds,
                "num_interruptions": s.num_interruptions,
                "num_context_switches": s.num_context_switches,
                "avg_resume_delay": (
                    sum(s.resume_delays_seconds) / len(s.resume_delays_seconds)
                    if s.resume_delays_seconds
                    else 0.0
                ),
                "avg_interruption_duration": (
                    sum(s.interruption_durations_seconds) / len(s.interruption_durations_seconds)
                    if s.interruption_durations_seconds
                    else 0.0
                ),
                "start_hour": s.start_time.hour,
            }
        )
    return pd.DataFrame(rows)


def discover_frequency_patterns(
    sessions: list[ReconstructedSession], min_sessions: int = 5, z_threshold: float = 1.0
) -> list[BehaviouralPattern]:
    """Detect (task_category, context) combinations with unusually high
    interruption or switch rates compared to the population mean.

    Uses a simple z-score over group-level rates; groups with too few
    sessions (< min_sessions) are skipped to avoid noisy conclusions.
    """
    df = _sessions_to_frame(sessions)
    if df.empty:
        return []

    df["interruption_rate"] = df["num_interruptions"] / df["session_duration_seconds"].replace(
        0, np.nan
    )
    df["switch_rate"] = df["num_context_switches"] / df["session_duration_seconds"].replace(
        0, np.nan
    )
    df = df.fillna(0.0)

    patterns: list[BehaviouralPattern] = []

    grouped = df.groupby(["task_category", "context"])
    pop_mean_int = df["interruption_rate"].mean()
    pop_std_int = df["interruption_rate"].std(ddof=0) or 1e-9
    pop_mean_switch = df["switch_rate"].mean()
    pop_std_switch = df["switch_rate"].std(ddof=0) or 1e-9

    for (task_category, context), group in grouped:
        if len(group) < min_sessions:
            continue

        group_int_rate = group["interruption_rate"].mean()
        group_switch_rate = group["switch_rate"].mean()

        z_int = (group_int_rate - pop_mean_int) / pop_std_int
        z_switch = (group_switch_rate - pop_mean_switch) / pop_std_switch

        if z_switch >= z_threshold:
            patterns.append(
                BehaviouralPattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type="frequency",
                    description=(
                        f"User frequently switches tasks during {task_category} "
                        f"in context '{context}'."
                    ),
                    evidence={
                        "task_category": task_category,
                        "context": context,
                        "sample_size": int(len(group)),
                        "group_switch_rate_per_second": round(float(group_switch_rate), 6),
                        "population_switch_rate_per_second": round(float(pop_mean_switch), 6),
                        "z_score": round(float(z_switch), 3),
                    },
                    confidence=round(float(min(1.0, max(0.0, (z_switch) / 4.0))), 3),
                )
            )

        if z_int >= z_threshold:
            patterns.append(
                BehaviouralPattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type="frequency",
                    description=(
                        f"Interruptions occur most frequently during {task_category} "
                        f"in context '{context}'."
                    ),
                    evidence={
                        "task_category": task_category,
                        "context": context,
                        "sample_size": int(len(group)),
                        "group_interruption_rate_per_second": round(float(group_int_rate), 6),
                        "population_interruption_rate_per_second": round(float(pop_mean_int), 6),
                        "z_score": round(float(z_int), 3),
                    },
                    confidence=round(float(min(1.0, max(0.0, (z_int) / 4.0))), 3),
                )
            )

    return patterns


def discover_resume_delay_pattern(
    sessions: list[ReconstructedSession], short_threshold_seconds: float = 30.0
) -> list[BehaviouralPattern]:
    """Detect the pattern 'short interruptions are followed by long resume delays'.

    Compares the average resume delay following short interruptions vs.
    following longer interruptions, using paired (duration, delay) samples
    collected per session (in this schema, an interruption's duration and
    its resume delay are the same measured interval — the model records
    the delay between INTERRUPTION and the next RESUME as one quantity).
    To still surface a meaningful signal, we instead compare each
    session's *shortest* interruption against its *average* resume delay
    across all its interruptions, flagging sessions where short
    interruptions correspond to a disproportionately long total resume
    delay burden.
    """
    patterns: list[BehaviouralPattern] = []
    candidate_sessions = []

    for s in sessions:
        if len(s.interruption_durations_seconds) < 2:
            continue
        durations = s.interruption_durations_seconds
        short = [d for d in durations if d <= short_threshold_seconds]
        long = [d for d in durations if d > short_threshold_seconds]
        if not short:
            continue
        avg_short = sum(short) / len(short)
        avg_resume_all = sum(s.resume_delays_seconds) / len(s.resume_delays_seconds) if s.resume_delays_seconds else 0.0
        if avg_resume_all > 0 and avg_short > 0 and avg_resume_all >= 2 * avg_short:
            candidate_sessions.append(
                {
                    "session_id": s.session_id,
                    "avg_short_interruption_seconds": round(avg_short, 2),
                    "avg_resume_delay_seconds": round(avg_resume_all, 2),
                }
            )

    if candidate_sessions:
        ratio = len(candidate_sessions) / max(len(sessions), 1)
        patterns.append(
            BehaviouralPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="frequency",
                description="Short interruptions are followed by disproportionately long resume delays.",
                evidence={
                    "matching_sessions": candidate_sessions[:20],
                    "matching_session_count": len(candidate_sessions),
                    "total_sessions": len(sessions),
                },
                confidence=round(min(1.0, ratio * 3), 3),
            )
        )

    return patterns


def discover_clusters(
    sessions: list[ReconstructedSession], n_clusters: int = 3, random_state: int = 42
) -> list[BehaviouralPattern]:
    """Cluster sessions by their timing-feature profile using KMeans.

    Returns one BehaviouralPattern per cluster describing its centroid
    in human-readable terms.
    """
    df = _sessions_to_frame(sessions)
    if len(df) < n_clusters:
        return []

    feature_cols = [
        "session_duration_seconds",
        "focused_time_seconds",
        "interruption_time_seconds",
        "num_interruptions",
        "num_context_switches",
        "avg_resume_delay",
    ]
    X = df[feature_cols].to_numpy()
    X_scaled = StandardScaler().fit_transform(X)

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(X_scaled)
    df["cluster"] = labels

    patterns: list[BehaviouralPattern] = []
    for cluster_id in sorted(df["cluster"].unique()):
        cluster_df = df[df["cluster"] == cluster_id]
        centroid = cluster_df[feature_cols].mean().to_dict()
        size = len(cluster_df)

        # Heuristic natural-language label based on relative interruption/switch load.
        if centroid["num_context_switches"] > df["num_context_switches"].mean() and centroid[
            "focused_time_seconds"
        ] < df["focused_time_seconds"].mean():
            label = "high-switch / low-focus sessions"
        elif centroid["interruption_time_seconds"] > df["interruption_time_seconds"].mean():
            label = "interruption-heavy sessions"
        else:
            label = "stable / focused sessions"

        patterns.append(
            BehaviouralPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="cluster",
                description=f"Cluster {cluster_id}: {label} ({size} sessions).",
                evidence={
                    "cluster_id": int(cluster_id),
                    "size": int(size),
                    "centroid": {k: round(float(v), 3) for k, v in centroid.items()},
                },
                confidence=round(size / len(df), 3),
            )
        )

    return patterns


def discover_anomalies(
    sessions: list[ReconstructedSession], contamination: float = 0.05, random_state: int = 42
) -> list[BehaviouralPattern]:
    """Flag sessions with unusual timing profiles using IsolationForest."""
    df = _sessions_to_frame(sessions)
    if len(df) < 10:
        return []

    feature_cols = [
        "session_duration_seconds",
        "focused_time_seconds",
        "interruption_time_seconds",
        "num_interruptions",
        "num_context_switches",
        "avg_resume_delay",
    ]
    X = df[feature_cols].to_numpy()
    X_scaled = StandardScaler().fit_transform(X)

    model = IsolationForest(contamination=contamination, random_state=random_state)
    preds = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)
    df["is_anomaly"] = preds == -1
    df["anomaly_score"] = scores

    patterns: list[BehaviouralPattern] = []
    anomalies = df[df["is_anomaly"]].sort_values("anomaly_score")

    for _, row in anomalies.iterrows():
        patterns.append(
            BehaviouralPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="anomaly",
                description=(
                    f"Session {row['session_id']} shows an unusual timing profile "
                    f"relative to other sessions."
                ),
                evidence={
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "task_category": row["task_category"],
                    "context": row["context"],
                    "anomaly_score": round(float(row["anomaly_score"]), 4),
                    "num_interruptions": int(row["num_interruptions"]),
                    "num_context_switches": int(row["num_context_switches"]),
                },
                confidence=round(float(min(1.0, max(0.0, -row["anomaly_score"] + 0.5))), 3),
            )
        )

    return patterns


def discover_all_patterns(sessions: list[ReconstructedSession]) -> list[BehaviouralPattern]:
    """Convenience wrapper running all pattern-discovery techniques."""
    patterns: list[BehaviouralPattern] = []
    patterns.extend(discover_frequency_patterns(sessions))
    patterns.extend(discover_resume_delay_pattern(sessions))
    patterns.extend(discover_clusters(sessions))
    patterns.extend(discover_anomalies(sessions))
    return patterns
