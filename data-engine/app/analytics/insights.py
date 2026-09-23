"""
Behavioral Insight Generators
==============================

Generates actionable insights from behavioral data to answer meaningful questions:
1. When am I most likely to forget tasks?
2. Which contexts are associated with forgetting?
3. Which task categories generate the most friction?
4. When do context switches happen most frequently?
5. How much time is lost to interruptions?
6. Which recurring task patterns are associated with delays?
7. Which locations/contexts are strongly associated with particular tasks?
8. What time periods show the highest cognitive friction?
9. Which behaviours are improving or worsening over time?
10. Which tasks should receive proactive attention?

Each insight follows the pattern: Behaviour → Pattern → Evidence → Risk → Recommendation
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict


def generate_forgetting_timing_insight(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: When am I most likely to forget tasks?
    
    Pattern Analysis: Identifies high-risk time periods for forgetting
    Evidence: Statistical analysis of forgetting rates by time dimensions
    Risk: Time periods with significantly elevated forgetting rates
    Recommendation: Schedule important tasks during low-risk periods
    """
    if tasks_df.empty:
        return {"insight_type": "forgetting_timing", "message": "Insufficient data"}
    
    resolved = tasks_df[tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
    if resolved.empty:
        return {"insight_type": "forgetting_timing", "message": "No resolved tasks yet"}
    
    # Analyze by weekday
    resolved["weekday"] = pd.to_datetime(resolved["created_at"]).dt.day_name()
    weekday_rates = resolved.groupby("weekday").apply(
        lambda g: len(g[g["status"] == "forgotten"]) / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    # Analyze by hour
    resolved["hour"] = pd.to_datetime(resolved["created_at"]).dt.hour
    hour_rates = resolved.groupby("hour").apply(
        lambda g: len(g[g["status"] == "forgotten"]) / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    # Find high-risk periods (top 20%)
    overall_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved)
    
    high_risk_weekdays = weekday_rates[weekday_rates > overall_rate * 1.5].index.tolist()
    high_risk_hours = hour_rates[hour_rates > overall_rate * 1.5].index.tolist()
    
    # Generate recommendation
    if high_risk_weekdays or high_risk_hours:
        message = f"You're {((max(weekday_rates) / overall_rate - 1) * 100):.0f}% more likely to forget tasks on {max(weekday_rates.index, key=lambda x: weekday_rates[x])}."
        if high_risk_hours:
            message += f" Avoid scheduling important tasks during {max(hour_rates.index, key=lambda x: hour_rates[x])}:00."
    else:
        message = "Your forgetting risk is relatively consistent across time periods."
    
    return {
        "insight_type": "forgetting_timing",
        "message": message,
        "evidence": {
            "overall_forgetting_rate": round(overall_rate, 4),
            "high_risk_weekdays": high_risk_weekdays,
            "high_risk_hours": high_risk_hours,
            "weekday_rates": {k: round(v, 4) for k, v in weekday_rates.to_dict().items()},
            "hour_rates": {str(k): round(v, 4) for k, v in hour_rates.to_dict().items()},
        },
        "risk_level": "HIGH" if len(high_risk_weekdays) > 2 else "MEDIUM" if len(high_risk_weekdays) > 0 else "LOW",
        "recommendation": "Schedule high-priority tasks during low-risk periods identified above."
    }


def generate_context_forgetting_insight(
    tasks_df: pd.DataFrame,
    location_labels: Dict
) -> Dict[str, any]:
    """
    Insight: Which contexts are associated with forgetting?
    
    Pattern Analysis: Identifies locations/categories with elevated forgetting rates
    Evidence: Statistical comparison of forgetting rates across contexts
    Risk: Contexts where forgetting is significantly more likely
    Recommendation: Modify environment or task allocation for high-risk contexts
    """
    if tasks_df.empty:
        return {"insight_type": "context_forgetting", "message": "Insufficient data"}
    
    resolved = tasks_df[tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
    if resolved.empty:
        return {"insight_type": "context_forgetting", "message": "No resolved tasks yet"}
    
    overall_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved)
    
    # Analyze by category
    category_rates = resolved.groupby("category").apply(
        lambda g: len(g[g["status"] == "forgotten"]) / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    # Analyze by location
    resolved_with_loc = resolved.dropna(subset=["location_id"])
    if not resolved_with_loc.empty:
        location_rates = resolved_with_loc.groupby("location_id").apply(
            lambda g: len(g[g["status"] == "forgotten"]) / len(g) if len(g) > 0 else 0.0,
            include_groups=False
        )
        location_rates_named = {location_labels.get(loc_id, str(loc_id)): round(rate, 4) 
                               for loc_id, rate in location_rates.items()}
    else:
        location_rates_named = {}
    
    # Identify high-risk contexts
    high_risk_categories = category_rates[category_rates > overall_rate * 1.3].index.tolist()
    high_risk_locations = [loc for loc, rate in location_rates_named.items() 
                          if rate > overall_rate * 1.3]
    
    if high_risk_categories:
        message = f"Tasks in '{high_risk_categories[0]}' category are {((category_rates[high_risk_categories[0]] / overall_rate - 1) * 100):.0f}% more likely to be forgotten."
    elif high_risk_locations:
        message = f"Tasks at '{high_risk_locations[0]}' are {((location_rates_named[high_risk_locations[0]] / overall_rate - 1) * 100):.0f}% more likely to be forgotten."
    else:
        message = "No specific contexts show significantly elevated forgetting risk."
    
    return {
        "insight_type": "context_forgetting",
        "message": message,
        "evidence": {
            "overall_forgetting_rate": round(overall_rate, 4),
            "category_rates": {k: round(v, 4) for k, v in category_rates.to_dict().items()},
            "location_rates": location_rates_named,
            "high_risk_categories": high_risk_categories,
            "high_risk_locations": high_risk_locations,
        },
        "risk_level": "HIGH" if len(high_risk_categories) > 1 else "MEDIUM" if high_risk_categories else "LOW",
        "recommendation": "Consider environmental modifications or task reallocation for high-risk contexts."
    }


def generate_category_friction_insight(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: Which task categories generate the most friction?
    
    Pattern Analysis: Measures behavioral friction by task category
    Evidence: Aggregated friction scores, interruption rates, context switches per category
    Risk: Categories with consistently high friction metrics
    Recommendation: Focus process improvement on high-friction categories
    """
    if tasks_df.empty or sessions_df.empty:
        return {"insight_type": "category_friction", "message": "Insufficient data"}
    
    # Merge sessions with tasks to get category
    merged = sessions_df.merge(tasks_df[["id", "category"]], left_on="task_id", right_on="id", how="left")
    
    # Calculate friction metrics per category
    category_metrics = {}
    for category in tasks_df["category"].unique():
        cat_tasks = tasks_df[tasks_df["category"] == category]
        cat_sessions = merged[merged["category"] == category]
        
        if cat_sessions.empty:
            continue
        
        # Forgetting rate
        resolved = cat_tasks[cat_tasks["status"].isin(["completed", "forgotten", "cancelled"])]
        forgetting_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved) if len(resolved) > 0 else 0.0
        
        # Interruption density
        cat_interruptions = interruptions_df[interruptions_df["task_id"].isin(cat_tasks["id"])]
        active_seconds = cat_sessions["focused_time_seconds"].sum() + cat_sessions["interruption_time_seconds"].sum()
        interruption_density = len(cat_interruptions) / (active_seconds / 3600.0) if active_seconds > 0 else 0.0
        
        # Context switch rate
        switch_rate = cat_sessions["context_switch_count"].sum() / len(cat_sessions) if len(cat_sessions) > 0 else 0.0
        
        # Composite friction score (normalized)
        friction_score = (forgetting_rate * 100 + interruption_density * 10 + switch_rate * 20)
        
        category_metrics[category] = {
            "forgetting_rate": round(forgetting_rate, 4),
            "interruption_density": round(interruption_density, 4),
            "switch_rate": round(switch_rate, 4),
            "friction_score": round(friction_score, 2),
        }
    
    if not category_metrics:
        return {"insight_type": "category_friction", "message": "No category data available"}
    
    # Find highest friction category
    highest_friction = max(category_metrics.keys(), key=lambda x: category_metrics[x]["friction_score"])
    avg_friction = np.mean([m["friction_score"] for m in category_metrics.values()])
    
    message = f"'{highest_friction}' tasks generate the most friction (score: {category_metrics[highest_friction]['friction_score']})."
    if category_metrics[highest_friction]["friction_score"] > avg_friction * 1.5:
        message += " This is significantly above average."
    
    return {
        "insight_type": "category_friction",
        "message": message,
        "evidence": {
            "category_metrics": category_metrics,
            "average_friction": round(avg_friction, 2),
        },
        "risk_level": "HIGH" if category_metrics[highest_friction]["friction_score"] > avg_friction * 1.5 else "MEDIUM",
        "recommendation": f"Process improvement efforts should prioritize '{highest_friction}' tasks."
    }


def generate_context_switch_timing_insight(
    sessions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: When do context switches happen most frequently?
    
    Pattern Analysis: Temporal patterns in context switching behavior
    Evidence: Distribution of context switches by time of day and day of week
    Risk: Time periods with excessive context switching
    Recommendation: Schedule deep work during low-switch periods
    """
    if sessions_df.empty:
        return {"insight_type": "context_switch_timing", "message": "Insufficient data"}
    
    sessions_df["weekday"] = pd.to_datetime(sessions_df["session_start"]).dt.day_name()
    sessions_df["hour"] = pd.to_datetime(sessions_df["session_start"]).dt.hour
    
    # Switches by weekday
    weekday_switches = sessions_df.groupby("weekday")["context_switch_count"].sum()
    
    # Switches by hour
    hour_switches = sessions_df.groupby("hour")["context_switch_count"].sum()
    
    # Calculate rates (switches per session)
    weekday_rates = sessions_df.groupby("weekday").apply(
        lambda g: g["context_switch_count"].sum() / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    hour_rates = sessions_df.groupby("hour").apply(
        lambda g: g["context_switch_count"].sum() / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    # Find peak switch times
    peak_weekday = weekday_rates.idxmax() if not weekday_rates.empty else None
    peak_hour = hour_rates.idxmax() if not hour_rates.empty else None
    
    avg_switch_rate = sessions_df["context_switch_count"].mean()
    
    if peak_weekday and weekday_rates[peak_weekday] > avg_switch_rate * 1.5:
        message = f"Context switching peaks on {peak_weekday} ({weekday_rates[peak_weekday]:.2f} switches/session vs {avg_switch_rate:.2f} average)."
    elif peak_hour and hour_rates[peak_hour] > avg_switch_rate * 1.5:
        message = f"Context switching peaks around {peak_hour}:00 ({hour_rates[peak_hour]:.2f} switches/session)."
    else:
        message = "Context switching is relatively evenly distributed throughout the week."
    
    return {
        "insight_type": "context_switch_timing",
        "message": message,
        "evidence": {
            "weekday_rates": {k: round(v, 2) for k, v in weekday_rates.to_dict().items()},
            "hour_rates": {str(k): round(v, 2) for k, v in hour_rates.to_dict().items()},
            "average_switch_rate": round(avg_switch_rate, 2),
            "peak_weekday": peak_weekday,
            "peak_hour": peak_hour,
        },
        "risk_level": "HIGH" if (peak_weekday and weekday_rates[peak_weekday] > avg_switch_rate * 2) else "MEDIUM",
        "recommendation": "Schedule focused work during periods with lower context switching."
    }


def generate_interruption_cost_insight(
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: How much time is lost to interruptions?
    
    Pattern Analysis: Quantifies time lost to direct interruptions and switching costs
    Evidence: Total interruption time + estimated cognitive switching overhead
    Risk: Significant time loss indicates productivity impact
    Recommendation: Implement interruption mitigation strategies
    """
    if interruptions_df.empty and sessions_df.empty:
        return {"insight_type": "interruption_cost", "message": "Insufficient data"}
    
    # Direct interruption time
    if not interruptions_df.empty:
        total_interruption_seconds = interruptions_df["duration_seconds"].sum()
        interruption_hours = total_interruption_seconds / 3600.0
    else:
        interruption_hours = 0.0
    
    # Context switch overhead (5 minutes per switch based on cognitive research)
    if not sessions_df.empty:
        total_switches = sessions_df["context_switch_count"].sum()
        switch_overhead_hours = (total_switches * 5) / 60.0  # 5 minutes per switch
    else:
        total_switches = 0
        switch_overhead_hours = 0.0
    
    total_time_lost = interruption_hours + switch_overhead_hours
    
    # Calculate as percentage of active time
    if not sessions_df.empty:
        active_hours = (sessions_df["focused_time_seconds"].sum() + sessions_df["interruption_time_seconds"].sum()) / 3600.0
        time_lost_percentage = (total_time_lost / active_hours * 100) if active_hours > 0 else 0.0
    else:
        time_lost_percentage = 0.0
    
    if total_time_lost > 2.0:  # More than 2 hours lost
        message = f"You're losing {total_time_lost:.1f} hours per week to interruptions ({time_lost_percentage:.1f}% of active time)."
    elif total_time_lost > 1.0:
        message = f"You're losing {total_time_lost:.1f} hours per week to interruptions."
    else:
        message = f"Interruption cost is relatively low ({total_time_lost:.1f} hours/week)."
    
    return {
        "insight_type": "interruption_cost",
        "message": message,
        "evidence": {
            "interruption_hours": round(interruption_hours, 2),
            "switch_overhead_hours": round(switch_overhead_hours, 2),
            "total_time_lost_hours": round(total_time_lost, 2),
            "time_lost_percentage": round(time_lost_percentage, 1),
            "total_switches": int(total_switches),
        },
        "risk_level": "HIGH" if total_time_lost > 2.0 else "MEDIUM" if total_time_lost > 1.0 else "LOW",
        "recommendation": "Consider implementing 'focus blocks' or notification management to reduce interruptions."
    }


def generate_recurring_pattern_insight(
    tasks_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: Which recurring task patterns are associated with delays?
    
    Pattern Analysis: Identifies recurring tasks with consistent delay patterns
    Evidence: Correlation between task recurrence and completion delays
    Risk: Recurring tasks that consistently get delayed
    Recommendation: Optimize scheduling or process for problematic recurring tasks
    """
    if tasks_df.empty or "deadline_at" not in tasks_df.columns or "completed_at" not in tasks_df.columns:
        return {"insight_type": "recurring_patterns", "message": "Insufficient data"}
    
    completed = tasks_df[tasks_df["status"] == "completed"].dropna(subset=["deadline_at", "completed_at"])
    if completed.empty:
        return {"insight_type": "recurring_patterns", "message": "No completed tasks with deadlines"}
    
    # Calculate delays
    completed["delay_minutes"] = (completed["completed_at"] - completed["deadline_at"]).dt.total_seconds() / 60.0
    completed["delayed"] = completed["delay_minutes"] > 0
    
    # Analyze by category
    category_delay_rates = completed.groupby("category").apply(
        lambda g: g["delayed"].sum() / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    # Analyze by priority
    priority_delay_rates = completed.groupby("priority").apply(
        lambda g: g["delayed"].sum() / len(g) if len(g) > 0 else 0.0,
        include_groups=False
    )
    
    overall_delay_rate = completed["delayed"].sum() / len(completed)
    
    # Find problematic patterns
    problematic_categories = category_delay_rates[category_delay_rates > overall_delay_rate * 1.3].index.tolist()
    problematic_priorities = priority_delay_rates[priority_delay_rates > overall_delay_rate * 1.3].index.tolist()
    
    if problematic_categories:
        worst_category = max(problematic_categories, key=lambda x: category_delay_rates[x])
        message = f"'{worst_category}' tasks are delayed {((category_delay_rates[worst_category] / overall_delay_rate - 1) * 100):.0f}% more often than average."
    elif problematic_priorities:
        worst_priority = max(problematic_priorities, key=lambda x: priority_delay_rates[x])
        message = f"'{worst_priority}' priority tasks are delayed {((priority_delay_rates[worst_priority] / overall_delay_rate - 1) * 100):.0f}% more often than average."
    else:
        message = "No specific recurring patterns show significantly elevated delay风险."
    
    return {
        "insight_type": "recurring_patterns",
        "message": message,
        "evidence": {
            "overall_delay_rate": round(overall_delay_rate, 4),
            "category_delay_rates": {k: round(v, 4) for k, v in category_delay_rates.to_dict().items()},
            "priority_delay_rates": {k: round(v, 4) for k, v in priority_delay_rates.to_dict().items()},
            "problematic_categories": problematic_categories,
            "problematic_priorities": problematic_priorities,
        },
        "risk_level": "HIGH" if len(problematic_categories) > 1 else "MEDIUM" if problematic_categories else "LOW",
        "recommendation": "Review scheduling and resource allocation for problematic task patterns."
    }


def generate_context_association_insight(
    tasks_df: pd.DataFrame,
    location_labels: Dict
) -> Dict[str, any]:
    """
    Insight: Which locations/contexts are strongly associated with particular tasks?
    
    Pattern Analysis: Measures strength of location-task associations
    Evidence: Statistical association metrics between locations and task categories
    Risk: Weak associations may indicate suboptimal task-context pairing
    Recommendation: Optimize task scheduling based on context strengths
    """
    if tasks_df.empty or not location_labels:
        return {"insight_type": "context_association", "message": "Insufficient data"}
    
    tasks_with_loc = tasks_df.dropna(subset=["location_id"])
    if tasks_with_loc.empty:
        return {"insight_type": "context_association", "message": "No location data available"}
    
    # Calculate association strength (normalized mutual information approximation)
    associations = {}
    for category in tasks_df["category"].unique():
        cat_tasks = tasks_with_loc[tasks_with_loc["category"] == category]
        if len(cat_tasks) == 0:
            continue
        
        location_counts = cat_tasks["location_id"].value_counts()
        total_cat_tasks = len(cat_tasks)
        
        # Association strength = (max_count / total) * (total / overall_category_count)
        max_loc = location_counts.idxmax()
        max_count = location_counts.max()
        association_strength = (max_count / total_cat_tasks)
        
        location_name = location_labels.get(max_loc, str(max_loc))
        associations[category] = {
            "primary_location": location_name,
            "association_strength": round(association_strength, 4),
            "location_count": int(max_count),
            "total_category_tasks": int(total_cat_tasks),
        }
    
    if not associations:
        return {"insight_type": "context_association", "message": "No associations found"}
    
    # Find strongest and weakest associations
    strongest = max(associations.keys(), key=lambda x: associations[x]["association_strength"])
    weakest = min(associations.keys(), key=lambda x: associations[x]["association_strength"])
    
    avg_association = np.mean([a["association_strength"] for a in associations.values()])
    
    message = f"'{strongest}' tasks are strongly associated with {associations[strongest]['primary_location']} ({associations[strongest]['association_strength']*100:.1f}%)."
    if associations[weakest]["association_strength"] < avg_association * 0.5:
        message += f" '{weakest}' tasks have weak location associations."
    
    return {
        "insight_type": "context_association",
        "message": message,
        "evidence": {
            "associations": associations,
            "average_association": round(avg_association, 4),
        },
        "risk_level": "MEDIUM" if associations[weakest]["association_strength"] < 0.3 else "LOW",
        "recommendation": "Consider scheduling tasks in their associated contexts for better consistency."
    }


def generate_cognitive_friction_timing_insight(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: What time periods show the highest cognitive friction?
    
    Pattern Analysis: Identifies time periods with highest behavioral friction
    Evidence: Composite friction score by time of day and day of week
    Risk: High-friction periods indicate suboptimal cognitive performance
    Recommendation: Schedule demanding tasks during low-friction periods
    """
    if sessions_df.empty or tasks_df.empty:
        return {"insight_type": "cognitive_friction_timing", "message": "Insufficient data"}
    
    # Merge data
    merged = sessions_df.merge(tasks_df[["id", "category", "status"]], left_on="task_id", right_on="id", how="left")
    
    # Add time dimensions
    merged["weekday"] = pd.to_datetime(merged["session_start"]).dt.day_name()
    merged["hour"] = pd.to_datetime(merged["session_start"]).dt.hour
    
    # Calculate friction per time period
    def calculate_friction(group):
        switches = group["context_switch_count"].sum()
        interruptions = group["interruption_count"].sum()
        active_time = group["focused_time_seconds"].sum() + group["interruption_time_seconds"].sum()
        
        if active_time == 0:
            return 0.0
        
        # Simple friction metric
        friction = (switches * 2 + interruptions) / (active_time / 3600.0)  # per hour
        return friction
    
    weekday_friction = merged.groupby("weekday").apply(calculate_friction, include_groups=False)
    hour_friction = merged.groupby("hour").apply(calculate_friction, include_groups=False)
    
    if weekday_friction.empty or hour_friction.empty:
        return {"insight_type": "cognitive_friction_timing", "message": "No friction data available"}
    
    # Find peak friction times
    peak_weekday = weekday_friction.idxmax()
    peak_hour = hour_friction.idxmax()
    avg_friction = weekday_friction.mean()
    
    if weekday_friction[peak_weekday] > avg_friction * 1.5:
        message = f"Cognitive friction peaks on {peak_weekday} ({weekday_friction[peak_weekday]:.2f} vs {avg_friction:.2f} average)."
    else:
        message = f"Cognitive friction is highest around {peak_hour}:00 ({hour_friction[peak_hour]:.2f})."
    
    return {
        "insight_type": "cognitive_friction_timing",
        "message": message,
        "evidence": {
            "weekday_friction": {k: round(v, 2) for k, v in weekday_friction.to_dict().items()},
            "hour_friction": {str(k): round(v, 2) for k, v in hour_friction.to_dict().items()},
            "average_friction": round(avg_friction, 2),
            "peak_weekday": peak_weekday,
            "peak_hour": peak_hour,
        },
        "risk_level": "HIGH" if weekday_friction[peak_weekday] > avg_friction * 2 else "MEDIUM",
        "recommendation": "Schedule cognitively demanding tasks during low-friction periods."
    }


def generate_trend_insight(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    window_days: int = 30
) -> Dict[str, any]:
    """
    Insight: Which behaviours are improving or worsening over time?
    
    Pattern Analysis: Computes trends for key behavioral metrics over time
    Evidence: Linear regression slopes for metrics over time windows
    Risk: Negative trends indicate worsening behavioral patterns
    Recommendation: Focus attention on metrics with negative trends
    """
    if tasks_df.empty:
        return {"insight_type": "behavioral_trends", "message": "Insufficient data"}
    
    cutoff = datetime.now() - timedelta(days=window_days)
    
    # Time series data preparation
    recent_tasks = tasks_df[tasks_df["created_at"] >= cutoff].copy()
    recent_tasks["date"] = pd.to_datetime(recent_tasks["created_at"]).dt.date
    
    # Calculate daily metrics
    daily_metrics = []
    for date in pd.date_range(start=cutoff.date(), end=datetime.now().date()):
        day_tasks = recent_tasks[recent_tasks["date"] == date]
        if day_tasks.empty:
            continue
        
        resolved = day_tasks[day_tasks["status"].isin(["completed", "forgotten", "cancelled"])]
        forgetting_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved) if len(resolved) > 0 else 0.0
        
        daily_metrics.append({
            "date": date,
            "forgetting_rate": forgetting_rate,
            "task_count": len(day_tasks),
        })
    
    if len(daily_metrics) < 7:
        return {"insight_type": "behavioral_trends", "message": "Insufficient time series data"}
    
    metrics_df = pd.DataFrame(daily_metrics)
    
    # Calculate trends (simple linear regression slope)
    def calculate_trend(series):
        if len(series) < 2:
            return 0.0
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series, 1)
        return slope
    
    forgetting_trend = calculate_trend(metrics_df["forgetting_rate"].values)
    
    # Interpret trends
    trends = {
        "forgetting_trend": round(forgetting_trend, 6),
        "trend_direction": "IMPROVING" if forgetting_trend < 0 else "WORSENING" if forgetting_trend > 0.001 else "STABLE",
    }
    
    if forgetting_trend > 0.001:
        message = f"Forgetting rate is worsening (trend: +{forgetting_trend*100:.4f}% per day)."
    elif forgetting_trend < -0.001:
        message = f"Forgetting rate is improving (trend: {forgetting_trend*100:.4f}% per day)."
    else:
        message = "Forgetting rate is relatively stable over time."
    
    return {
        "insight_type": "behavioral_trends",
        "message": message,
        "evidence": {
            "trends": trends,
            "current_forgetting_rate": round(metrics_df["forgetting_rate"].iloc[-1], 4),
            "period_days": window_days,
            "data_points": len(metrics_df),
        },
        "risk_level": "HIGH" if forgetting_trend > 0.005 else "MEDIUM" if forgetting_trend > 0.001 else "LOW",
        "recommendation": "Continue monitoring trends and investigate any significant worsening patterns."
    }


def generate_proactive_attention_insight(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame
) -> Dict[str, any]:
    """
    Insight: Which tasks should receive proactive attention?
    
    Pattern Analysis: Identifies high-risk tasks needing intervention
    Evidence: Multi-factor risk assessment combining forgetting risk, friction, urgency
    Risk: Tasks with high composite risk scores
    Recommendation: Prioritize or provide support for identified high-risk tasks
    """
    if tasks_df.empty:
        return {"insight_type": "proactive_attention", "message": "Insufficient data"}
    
    # Focus on active tasks
    active_tasks = tasks_df[~tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
    if active_tasks.empty:
        return {"insight_type": "proactive_attention", "message": "No active tasks requiring attention"}
    
    # Calculate risk scores for active tasks
    task_risks = []
    
    for _, task in active_tasks.iterrows():
        risk_score = 0.0
        risk_factors = []
        
        # Priority factor
        if task["priority"] == "HIGH":
            risk_score += 0.3
            risk_factors.append("high_priority")
        elif task["priority"] == "MEDIUM":
            risk_score += 0.15
            risk_factors.append("medium_priority")
        
        # Deadline urgency
        if "deadline_at" in tasks_df.columns and pd.notna(task["deadline_at"]):
            days_until_deadline = (task["deadline_at"] - datetime.now()).total_seconds() / 86400
            if days_until_deadline < 1:
                risk_score += 0.4
                risk_factors.append("urgent_deadline")
            elif days_until_deadline < 3:
                risk_score += 0.2
                risk_factors.append("near_deadline")
        
        # Category risk (based on historical forgetting)
        category_tasks = tasks_df[tasks_df["category"] == task["category"]]
        resolved = category_tasks[category_tasks["status"].isin(["completed", "forgotten", "cancelled"])]
        if len(resolved) > 0:
            category_forgetting_rate = len(resolved[resolved["status"] == "forgotten"]) / len(resolved)
            if category_forgetting_rate > 0.3:
                risk_score += 0.2
                risk_factors.append("high_risk_category")
        
        task_risks.append({
            "task_id": str(task["id"]),
            "title": task["title"],
            "category": task["category"],
            "priority": task["priority"],
            "risk_score": round(risk_score, 4),
            "risk_factors": risk_factors,
        })
    
    # Sort by risk and get top priorities
    task_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    high_risk_tasks = [t for t in task_risks if t["risk_score"] > 0.5][:5]
    
    if not high_risk_tasks:
        return {
            "insight_type": "proactive_attention",
            "message": "No tasks require immediate proactive attention.",
            "evidence": {"total_active_tasks": len(active_tasks), "high_risk_count": 0},
            "risk_level": "LOW",
            "recommendation": "Continue regular task monitoring."
        }
    
    top_task = high_risk_tasks[0]
    message = f"'{top_task['title']}' ({top_task['category']}, {top_task['priority']}) needs proactive attention due to: {', '.join(top_task['risk_factors'])}."
    
    return {
        "insight_type": "proactive_attention",
        "message": message,
        "evidence": {
            "high_risk_tasks": high_risk_tasks,
            "total_active_tasks": len(active_tasks),
            "high_risk_count": len(high_risk_tasks),
        },
        "risk_level": "HIGH" if len(high_risk_tasks) > 2 else "MEDIUM",
        "recommendation": "Prioritize high-risk tasks and consider providing additional support or resources."
    }


def generate_all_insights(
    tasks_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    location_labels: Dict
) -> List[Dict]:
    """
    Generate all behavioral insights for comprehensive analysis.
    
    Returns a list of insight dictionaries following the pattern:
    Behaviour → Pattern → Evidence → Risk → Recommendation
    """
    insights = []
    
    try:
        insights.append(generate_forgetting_timing_insight(tasks_df, sessions_df))
    except Exception as e:
        insights.append({"insight_type": "forgetting_timing", "error": str(e)})
    
    try:
        insights.append(generate_context_forgetting_insight(tasks_df, location_labels))
    except Exception as e:
        insights.append({"insight_type": "context_forgetting", "error": str(e)})
    
    try:
        insights.append(generate_category_friction_insight(tasks_df, sessions_df, interruptions_df))
    except Exception as e:
        insights.append({"insight_type": "category_friction", "error": str(e)})
    
    try:
        insights.append(generate_context_switch_timing_insight(sessions_df))
    except Exception as e:
        insights.append({"insight_type": "context_switch_timing", "error": str(e)})
    
    try:
        insights.append(generate_interruption_cost_insight(interruptions_df, sessions_df))
    except Exception as e:
        insights.append({"insight_type": "interruption_cost", "error": str(e)})
    
    try:
        insights.append(generate_recurring_pattern_insight(tasks_df))
    except Exception as e:
        insights.append({"insight_type": "recurring_patterns", "error": str(e)})
    
    try:
        insights.append(generate_context_association_insight(tasks_df, location_labels))
    except Exception as e:
        insights.append({"insight_type": "context_association", "error": str(e)})
    
    try:
        insights.append(generate_cognitive_friction_timing_insight(tasks_df, sessions_df, interruptions_df))
    except Exception as e:
        insights.append({"insight_type": "cognitive_friction_timing", "error": str(e)})
    
    try:
        insights.append(generate_trend_insight(tasks_df, sessions_df, interruptions_df))
    except Exception as e:
        insights.append({"insight_type": "behavioral_trends", "error": str(e)})
    
    try:
        insights.append(generate_proactive_attention_insight(tasks_df, sessions_df, interruptions_df))
    except Exception as e:
        insights.append({"insight_type": "proactive_attention", "error": str(e)})
    
    return insights
