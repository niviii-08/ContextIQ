"""
Derived Behavioral Metrics
===========================

Mathematically defensible composite metrics that go beyond simple aggregates.
Each metric includes a clear formula, interpretation, and traceability to raw data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


def compute_forget_risk(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    window_days: int = 7
) -> Dict[str, float]:
    """
    Forget Risk Metric: Probability that a task will be forgotten based on recent patterns.
    
    Formula:
        forget_risk = 0.4 * recent_forgetting_rate 
                   + 0.3 * interruption_density
                   + 0.2 * context_switch_frequency
                   + 0.1 * deadline_pressure_ratio
    
    Where:
        - recent_forgetting_rate = forgotten_tasks / total_resolved_tasks (last window_days)
        - interruption_density = interruptions / active_hours
        - context_switch_frequency = context_switches / sessions
        - deadline_pressure_ratio = tasks_with_near_deadline / total_active_tasks
    
    Interpretation: 0-1 scale, higher = higher risk of forgetting
    Traceability: Computed from tasks, sessions, interruptions tables
    """
    if tasks_df.empty:
        return {"forget_risk": 0.0, "components": {}}
    
    # Time window
    cutoff = datetime.now() - timedelta(days=window_days)
    recent_tasks = tasks_df[tasks_df["created_at"] >= cutoff] if "created_at" in tasks_df.columns else tasks_df
    
    # Recent forgetting rate
    resolved = recent_tasks[recent_tasks["status"].isin(["completed", "forgotten", "cancelled"])]
    if len(resolved) > 0:
        recent_forgotten = len(resolved[resolved["status"] == "forgotten"])
        recent_forgetting_rate = recent_forgotten / len(resolved)
    else:
        recent_forgetting_rate = 0.0
    
    # Interruption density
    if not sessions_df.empty and not interruptions_df.empty:
        total_active_seconds = (sessions_df["focused_time_seconds"] + sessions_df["interruption_time_seconds"]).sum()
        if total_active_seconds > 0:
            active_hours = total_active_seconds / 3600.0
            interruption_density = len(interruptions_df) / active_hours if active_hours > 0 else 0.0
        else:
            interruption_density = 0.0
    else:
        interruption_density = 0.0
    
    # Context switch frequency
    if not sessions_df.empty and len(sessions_df) > 0:
        context_switch_frequency = sessions_df["context_switch_count"].sum() / len(sessions_df)
    else:
        context_switch_frequency = 0.0
    
    # Deadline pressure ratio
    if "deadline_at" in tasks_df.columns:
        near_deadline_threshold = datetime.now() + timedelta(days=1)
        active_tasks = tasks_df[~tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
        if len(active_tasks) > 0:
            near_deadline = active_tasks[active_tasks["deadline_at"] <= near_deadline_threshold]
            deadline_pressure_ratio = len(near_deadline) / len(active_tasks)
        else:
            deadline_pressure_ratio = 0.0
    else:
        deadline_pressure_ratio = 0.0
    
    # Normalize components to 0-1 range
    norm_forgetting = min(1.0, recent_forgetting_rate * 2)  # Scale up since typical rates are low
    norm_interruption = min(1.0, interruption_density / 6.0)  # 6/hr saturation
    norm_switch = min(1.0, context_switch_frequency / 3.0)  # 3/session saturation
    norm_deadline = deadline_pressure_ratio
    
    forget_risk = (0.4 * norm_forgetting + 
                   0.3 * norm_interruption + 
                   0.2 * norm_switch + 
                   0.1 * norm_deadline)
    
    return {
        "forget_risk": round(min(1.0, forget_risk), 4),
        "components": {
            "recent_forgetting_rate": round(recent_forgetting_rate, 4),
            "interruption_density": round(interruption_density, 4),
            "context_switch_frequency": round(context_switch_frequency, 4),
            "deadline_pressure_ratio": round(deadline_pressure_ratio, 4),
        }
    }


def compute_context_switch_rate(
    sessions_df: pd.DataFrame,
    window_hours: int = 24
) -> Dict[str, float]:
    """
    Context Switch Rate: Frequency of context switches per unit time.
    
    Formula:
        context_switch_rate = total_context_switches / total_active_time_hours
    
    Interpretation: switches per hour, higher = more fragmented attention
    Traceability: Computed from context_sessions table
    """
    if sessions_df.empty:
        return {"context_switch_rate": 0.0, "total_switches": 0, "active_hours": 0.0}
    
    cutoff = datetime.now() - timedelta(hours=window_hours)
    recent_sessions = sessions_df[sessions_df["session_start"] >= cutoff] if "session_start" in sessions_df.columns else sessions_df
    
    total_switches = recent_sessions["context_switch_count"].sum()
    total_active_seconds = (recent_sessions["focused_time_seconds"] + recent_sessions["interruption_time_seconds"]).sum()
    active_hours = total_active_seconds / 3600.0 if total_active_seconds > 0 else 0.0
    
    context_switch_rate = total_switches / active_hours if active_hours > 0 else 0.0
    
    return {
        "context_switch_rate": round(context_switch_rate, 4),
        "total_switches": int(total_switches),
        "active_hours": round(active_hours, 2),
    }


def compute_interruption_rate(
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    window_hours: int = 24
) -> Dict[str, float]:
    """
    Interruption Rate: Frequency of interruptions per unit active time.
    
    Formula:
        interruption_rate = total_interruptions / total_active_time_hours
        
    Interpretation: interruptions per hour, higher = more disrupted work
    Traceability: Computed from interruptions and context_sessions tables
    """
    if interruptions_df.empty or sessions_df.empty:
        return {"interruption_rate": 0.0, "total_interruptions": 0, "active_hours": 0.0}
    
    cutoff = datetime.now() - timedelta(hours=window_hours)
    recent_interruptions = interruptions_df[interruptions_df["start_time"] >= cutoff] if "start_time" in interruptions_df.columns else interruptions_df
    recent_sessions = sessions_df[sessions_df["session_start"] >= cutoff] if "session_start" in sessions_df.columns else sessions_df
    
    total_interruptions = len(recent_interruptions)
    total_active_seconds = (recent_sessions["focused_time_seconds"] + recent_sessions["interruption_time_seconds"]).sum()
    active_hours = total_active_seconds / 3600.0 if total_active_seconds > 0 else 0.0
    
    interruption_rate = total_interruptions / active_hours if active_hours > 0 else 0.0
    
    return {
        "interruption_rate": round(interruption_rate, 4),
        "total_interruptions": total_interruptions,
        "active_hours": round(active_hours, 2),
    }


def compute_recovery_time(
    sessions_df: pd.DataFrame,
    window_days: int = 7
) -> Dict[str, float]:
    """
    Recovery Time: Average time to return to a paused task.
    
    Formula:
        recovery_time = mean(resume_delay_seconds) for sessions with resume_delay
    
    Interpretation: seconds, higher = slower recovery from interruptions
    Traceability: Computed from context_sessions.resume_delay_seconds
    """
    if sessions_df.empty:
        return {"recovery_time_seconds": 0.0, "recovery_time_minutes": 0.0, "sample_size": 0}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    recent_sessions = sessions_df[sessions_df["session_start"] >= cutoff] if "session_start" in sessions_df.columns else sessions_df
    
    resume_delays = recent_sessions["resume_delay_seconds"].dropna()
    if resume_delays.empty:
        return {"recovery_time_seconds": 0.0, "recovery_time_minutes": 0.0, "sample_size": 0}
    
    recovery_time_seconds = float(resume_delays.mean())
    
    return {
        "recovery_time_seconds": round(recovery_time_seconds, 2),
        "recovery_time_minutes": round(recovery_time_seconds / 60.0, 2),
        "sample_size": len(resume_delays),
    }


def compute_behavioral_friction_score(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame, 
    interruptions_df: pd.DataFrame
) -> Dict[str, float]:
    """
    Behavioral Friction Score: Composite measure of workflow disruption.
    
    Formula:
        friction_score = 0.35 * forgetting_component
                      + 0.25 * interruption_component
                      + 0.20 * context_switch_component
                      + 0.20 * recovery_component
    
    Where each component is normalized 0-100 based on saturation thresholds.
    
    Interpretation: 0-100 scale, higher = more behavioral friction
    Traceability: Computed from tasks, sessions, interruptions tables
    """
    # Forgetting component
    resolved = tasks_df[tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
    if len(resolved) > 0:
        forgetting_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved)
        forgetting_component = min(100.0, forgetting_rate * 200)  # Scale for sensitivity
    else:
        forgetting_component = 0.0
    
    # Interruption component
    if not sessions_df.empty:
        total_active_seconds = (sessions_df["focused_time_seconds"] + sessions_df["interruption_time_seconds"]).sum()
        if total_active_seconds > 0:
            active_hours = total_active_seconds / 3600.0
            interruption_rate = len(interruptions_df) / active_hours if active_hours > 0 else 0.0
            interruption_component = min(100.0, (interruption_rate / 8.0) * 100)  # 8/hr saturation
        else:
            interruption_component = 0.0
    else:
        interruption_component = 0.0
    
    # Context switch component
    if not sessions_df.empty and len(sessions_df) > 0:
        switches_per_session = sessions_df["context_switch_count"].sum() / len(sessions_df)
        context_switch_component = min(100.0, (switches_per_session / 4.0) * 100)  # 4/session saturation
    else:
        context_switch_component = 0.0
    
    # Recovery component
    if not sessions_df.empty:
        resume_delays = sessions_df["resume_delay_seconds"].dropna()
        if not resume_delays.empty:
            avg_recovery_minutes = resume_delays.mean() / 60.0
            recovery_component = min(100.0, (avg_recovery_minutes / 45.0) * 100)  # 45min saturation
        else:
            recovery_component = 0.0
    else:
        recovery_component = 0.0
    
    friction_score = (0.35 * forgetting_component + 
                      0.25 * interruption_component + 
                      0.20 * context_switch_component + 
                      0.20 * recovery_component)
    
    return {
        "friction_score": round(min(100.0, friction_score), 2),
        "components": {
            "forgetting_component": round(forgetting_component, 2),
            "interruption_component": round(interruption_component, 2),
            "context_switch_component": round(context_switch_component, 2),
            "recovery_component": round(recovery_component, 2),
        }
    }


def compute_completion_reliability(
    tasks_df: pd.DataFrame,
    window_days: int = 30
) -> Dict[str, float]:
    """
    Completion Reliability: Consistency of task completion over time.
    
    Formula:
        completion_reliability = 1 - std(completion_rate_by_day) / mean(completion_rate_by_day)
        
    Where completion_rate_by_day is computed for each day in the window.
    
    Interpretation: 0-1 scale, higher = more consistent completion patterns
    Traceability: Computed from tasks.status and tasks.created_at/completed_at
    """
    if tasks_df.empty:
        return {"completion_reliability": 0.0, "mean_daily_rate": 0.0, "std_daily_rate": 0.0}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    recent_tasks = tasks_df[tasks_df["created_at"] >= cutoff] if "created_at" in tasks_df.columns else tasks_df
    
    if "completed_at" not in recent_tasks.columns:
        return {"completion_reliability": 0.0, "mean_daily_rate": 0.0, "std_daily_rate": 0.0}
    
    # Compute daily completion rates
    recent_tasks["completion_date"] = pd.to_datetime(recent_tasks["completed_at"]).dt.date
    daily_stats = recent_tasks.groupby("completion_date").apply(
        lambda g: len(g[g["status"] == "completed"]) / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    if len(daily_stats) < 2:
        return {"completion_reliability": 0.5, "mean_daily_rate": 0.0, "std_daily_rate": 0.0}
    
    mean_rate = daily_stats.mean()
    std_rate = daily_stats.std()
    
    if mean_rate > 0:
        reliability = max(0.0, 1.0 - (std_rate / mean_rate))
    else:
        reliability = 0.0
    
    return {
        "completion_reliability": round(min(1.0, reliability), 4),
        "mean_daily_rate": round(mean_rate, 4),
        "std_daily_rate": round(std_rate, 4),
        "sample_days": len(daily_stats),
    }


def compute_context_consistency(
    tasks_df: pd.DataFrame,
    location_labels: Dict,
    window_days: int = 30
) -> Dict[str, float]:
    """
    Context Consistency: How consistently tasks are performed in their typical contexts.
    
    Formula:
        context_consistency = mean(category_location_match_rate)
        
    Where category_location_match_rate is computed per category as:
        (most_common_location_count / total_category_tasks)
    
    Interpretation: 0-1 scale, higher = more consistent context-task associations
    Traceability: Computed from tasks.category, tasks.location_id
    """
    if tasks_df.empty or not location_labels:
        return {"context_consistency": 0.0, "category_scores": {}}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    recent_tasks = tasks_df[tasks_df["created_at"] >= cutoff] if "created_at" in tasks_df.columns else tasks_df
    
    category_scores = {}
    
    for category in recent_tasks["category"].unique():
        cat_tasks = recent_tasks[recent_tasks["category"] == category]
        if len(cat_tasks) == 0:
            continue
            
        location_counts = cat_tasks["location_id"].value_counts()
        if len(location_counts) > 0:
            most_common_count = location_counts.iloc[0]
            consistency = most_common_count / len(cat_tasks)
            category_scores[category] = round(consistency, 4)
    
    if category_scores:
        overall_consistency = np.mean(list(category_scores.values()))
    else:
        overall_consistency = 0.0
    
    return {
        "context_consistency": round(overall_consistency, 4),
        "category_scores": category_scores,
    }


def compute_repetition_strength(
    tasks_df: pd.DataFrame,
    window_days: int = 30
) -> Dict[str, float]:
    """
    Repetition Strength: How strongly task patterns repeat over time.
    
    Formula:
        repetition_strength = mean(temporal_correlation_by_category)
        
    Where temporal_correlation measures autocorrelation of task creation
        frequency for each category at lag=7 days.
    
    Interpretation: 0-1 scale, higher = stronger repeating patterns
    Traceability: Computed from tasks.category and tasks.created_at
    """
    if tasks_df.empty or "created_at" not in tasks_df.columns:
        return {"repetition_strength": 0.0, "category_strengths": {}}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    recent_tasks = tasks_df[tasks_df["created_at"] >= cutoff].copy()
    recent_tasks["date"] = pd.to_datetime(recent_tasks["created_at"]).dt.date
    
    category_strengths = {}
    
    for category in recent_tasks["category"].unique():
        cat_tasks = recent_tasks[recent_tasks["category"] == category]
        daily_counts = cat_tasks.groupby("date").size()
        
        if len(daily_counts) < 14:  # Need at least 2 weeks for correlation
            category_strengths[category] = 0.0
            continue
        
        # Compute autocorrelation at 7-day lag
        try:
            series = daily_counts.reindex(pd.date_range(start=daily_counts.index.min(), 
                                                       end=daily_counts.index.max()), 
                                         fill_value=0)
            if len(series) >= 14:
                autocorr = series.autocorr(lag=7)
                category_strengths[category] = round(max(0.0, autocorr), 4) if not np.isnan(autocorr) else 0.0
            else:
                category_strengths[category] = 0.0
        except:
            category_strengths[category] = 0.0
    
    if category_strengths:
        overall_strength = np.mean(list(category_strengths.values()))
    else:
        overall_strength = 0.0
    
    return {
        "repetition_strength": round(overall_strength, 4),
        "category_strengths": category_strengths,
    }


def compute_time_lost_to_interruptions(
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    window_days: int = 7
) -> Dict[str, float]:
    """
    Time Lost to Interruptions: Total time lost due to interruptions.
    
    Formula:
        time_lost_hours = total_interruption_duration_hours + (context_switches * recovery_overhead)
        
    Where recovery_overhead is estimated as 5 minutes per context switch
        (based on research showing cognitive switching costs).
    
    Interpretation: hours, higher = more time lost to disruptions
    Traceability: Computed from interruptions.duration_seconds and sessions.context_switch_count
    """
    if interruptions_df.empty and sessions_df.empty:
        return {"time_lost_hours": 0.0, "interruption_hours": 0.0, "switch_overhead_hours": 0.0}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    
    # Direct interruption time
    if not interruptions_df.empty:
        recent_interruptions = interruptions_df[interruptions_df["start_time"] >= cutoff] if "start_time" in interruptions_df.columns else interruptions_df
        interruption_seconds = recent_interruptions["duration_seconds"].sum()
        interruption_hours = interruption_seconds / 3600.0
    else:
        interruption_hours = 0.0
    
    # Context switch overhead (5 minutes per switch based on cognitive research)
    RECOVERY_OVERHEAD_MINUTES = 5.0
    if not sessions_df.empty:
        recent_sessions = sessions_df[sessions_df["session_start"] >= cutoff] if "session_start" in sessions_df.columns else sessions_df
        total_switches = recent_sessions["context_switch_count"].sum()
        switch_overhead_hours = (total_switches * RECOVERY_OVERHEAD_MINUTES) / 60.0
    else:
        switch_overhead_hours = 0.0
    
    time_lost_hours = interruption_hours + switch_overhead_hours
    
    return {
        "time_lost_hours": round(time_lost_hours, 2),
        "interruption_hours": round(interruption_hours, 2),
        "switch_overhead_hours": round(switch_overhead_hours, 2),
        "total_switches": int(total_switches) if not sessions_df.empty else 0,
    }
