from datetime import datetime, timedelta, timezone
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics import metrics as m
from app.analytics import friction as f
from app.analytics import derived_metrics as dm
from app.analytics import insights as ins
from app.analytics import statistical_analysis as sa
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    OverviewResponse,
    TaskAnalyticsResponse,
    InterruptionAnalyticsResponse,
    ContextAnalyticsResponse,
    FrictionScoreResponse,
    DerivedMetricsResponse,
    InsightResponse,
    AllInsightsResponse,
    TrendAnalysisResponse,
    DistributionResponse,
    CorrelationResponse,
    StoryAnalyticsResponse,
    ContextSwitchTimelineResponse,
    TaskContextHeatmapResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _require_user(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _since(period_days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=period_days)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    return OverviewResponse(
        user_id=str(user_id),
        period_days=period_days,
        task_completion_rate=m.task_completion_rate(tasks_df),
        task_forgetting_rate=m.task_forgetting_rate(tasks_df),
        average_task_duration_minutes=m.average_task_duration_minutes(tasks_df),
        average_task_delay_minutes=m.average_task_delay_minutes(tasks_df),
        tasks_per_day=m.tasks_per_day(tasks_df, period_days),
        tasks_per_category=m.tasks_per_category(tasks_df),
        tasks_per_location=m.tasks_per_location(tasks_df, location_labels),
        total_tasks=int(len(tasks_df)),
        total_interruptions=m.interruption_count(interruptions_df),
        total_context_switches=m.total_context_switches(sessions_df),
    )


@router.get("/tasks", response_model=TaskAnalyticsResponse)
def get_task_analytics(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)
    tasks_df = m.load_tasks_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    return TaskAnalyticsResponse(
        user_id=str(user_id),
        period_days=period_days,
        total_tasks=int(len(tasks_df)),
        completion_rate=m.task_completion_rate(tasks_df),
        forgetting_rate=m.task_forgetting_rate(tasks_df),
        average_duration_minutes=m.average_task_duration_minutes(tasks_df),
        average_delay_minutes=m.average_task_delay_minutes(tasks_df),
        tasks_per_day=m.tasks_per_day(tasks_df, period_days),
        tasks_per_category=m.tasks_per_category(tasks_df),
        tasks_per_location=m.tasks_per_location(tasks_df, location_labels),
        forgetting_by_weekday=m.forgetting_by_weekday(tasks_df),
        forgetting_by_hour=m.forgetting_by_hour(tasks_df),
        forgetting_by_category=m.forgetting_by_category(tasks_df),
        forgetting_by_location=m.forgetting_by_location(tasks_df, location_labels),
    )


@router.get("/interruptions", response_model=InterruptionAnalyticsResponse)
def get_interruption_analytics(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)

    return InterruptionAnalyticsResponse(
        user_id=str(user_id),
        period_days=period_days,
        interruption_count=m.interruption_count(interruptions_df),
        interruption_duration_minutes_total=m.interruption_duration_minutes_total(interruptions_df),
        interruption_duration_minutes_avg=m.interruption_duration_minutes_avg(interruptions_df),
        interruption_by_weekday=m.interruption_by_weekday(interruptions_df),
        interruption_by_hour=m.interruption_by_hour(interruptions_df),
        interruption_by_category=m.interruption_by_category(interruptions_df),
    )


@router.get("/context", response_model=ContextAnalyticsResponse)
def get_context_analytics(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)
    sessions_df = m.load_sessions_df(db, user_id, since=since)
    tasks_df = m.load_tasks_df(db, user_id, since=since)
    events_df = m.load_events_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    return ContextAnalyticsResponse(
        user_id=str(user_id),
        period_days=period_days,
        total_sessions=int(len(sessions_df)),
        average_focus_session_minutes=m.average_focus_session_minutes(sessions_df),
        total_context_switches=m.total_context_switches(sessions_df),
        resume_count=m.resume_count(sessions_df),
        pause_count=m.pause_count(events_df),
        average_resume_delay_seconds=m.average_resume_delay_seconds(sessions_df),
        context_switching_by_task_category=m.context_switching_by_task_category(sessions_df, tasks_df),
        context_switching_by_location=m.context_switching_by_location(sessions_df, location_labels),
    )


@router.get("/friction", response_model=FrictionScoreResponse)
def get_friction_score(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)

    total_active_seconds = 0.0
    if not sessions_df.empty:
        total_active_seconds = float(
            (sessions_df["focused_time_seconds"] + sessions_df["interruption_time_seconds"]).sum()
        )

    result = f.compute_friction_score(
        task_forgetting_rate=m.task_forgetting_rate(tasks_df),
        interruption_count=m.interruption_count(interruptions_df),
        total_active_seconds=total_active_seconds,
        total_context_switches=m.total_context_switches(sessions_df),
        total_sessions=int(len(sessions_df)),
        average_resume_delay_seconds=m.average_resume_delay_seconds(sessions_df),
    )

    return FrictionScoreResponse(
        user_id=str(user_id),
        period_days=period_days,
        **result,
    )


@router.get("/derived-metrics", response_model=DerivedMetricsResponse)
def get_derived_metrics(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Get advanced derived metrics including forget risk, friction scores, etc."""
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    return DerivedMetricsResponse(
        user_id=str(user_id),
        period_days=period_days,
        forget_risk=dm.compute_forget_risk(tasks_df, sessions_df, interruptions_df, window_days=7),
        context_switch_rate=dm.compute_context_switch_rate(sessions_df, window_hours=24),
        interruption_rate=dm.compute_interruption_rate(interruptions_df, sessions_df, window_hours=24),
        recovery_time=dm.compute_recovery_time(sessions_df, window_days=7),
        behavioral_friction_score=dm.compute_behavioral_friction_score(tasks_df, sessions_df, interruptions_df),
        completion_reliability=dm.compute_completion_reliability(tasks_df, window_days=30),
        context_consistency=dm.compute_context_consistency(tasks_df, location_labels, window_days=30),
        repetition_strength=dm.compute_repetition_strength(tasks_df, window_days=30),
        time_lost_to_interruptions=dm.compute_time_lost_to_interruptions(interruptions_df, sessions_df, window_days=7),
    )


@router.get("/insights", response_model=AllInsightsResponse)
def get_all_insights(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Get all behavioral insights answering key questions about behavior patterns."""
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    all_insights = ins.generate_all_insights(tasks_df, sessions_df, interruptions_df, location_labels)

    return AllInsightsResponse(
        user_id=str(user_id),
        period_days=period_days,
        insights=[InsightResponse(**insight) for insight in all_insights],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/trends/{metric_name}", response_model=TrendAnalysisResponse)
def get_trend_analysis(
    metric_name: str,
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=7, le=3650),
    db: Session = Depends(get_db),
):
    """Get trend analysis for a specific metric over time."""
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    
    # Map metric names to data series
    if metric_name == "forgetting_rate":
        resolved = tasks_df[tasks_df["status"].isin(["completed", "forgotten", "cancelled"])]
        if resolved.empty:
            raise HTTPException(status_code=404, detail="No resolved tasks for trend analysis")
        resolved["date"] = pd.to_datetime(resolved["created_at"]).dt.date
        daily_rates = resolved.groupby("date").apply(
            lambda g: len(g[g["status"] == "forgotten"]) / len(g) if len(g) > 0 else 0.0,
            include_groups=False
        )
        series = daily_rates
        dates = pd.to_datetime(daily_rates.index)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric_name}")

    trend_result = sa.compute_trend_analysis(series, dates)

    if "error" in trend_result:
        raise HTTPException(status_code=400, detail=trend_result["error"])

    return TrendAnalysisResponse(
        user_id=str(user_id),
        period_days=period_days,
        metric_name=metric_name,
        **trend_result,
    )


@router.get("/distributions/{metric_name}", response_model=DistributionResponse)
def get_distribution(
    metric_name: str,
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Get distribution statistics for a specific metric."""
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)

    # Map metric names to data series
    if metric_name == "task_duration":
        completed = tasks_df[tasks_df["status"] == "completed"].dropna(subset=["started_at", "completed_at"])
        if completed.empty:
            raise HTTPException(status_code=404, detail="No completed tasks with duration data")
        series = (completed["completed_at"] - completed["started_at"]).dt.total_seconds() / 60.0
    elif metric_name == "session_duration":
        if sessions_df.empty:
            raise HTTPException(status_code=404, detail="No session data")
        series = (sessions_df["focused_time_seconds"] + sessions_df["interruption_time_seconds"]) / 60.0
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric_name}")

    dist_stats = sa.compute_distribution_statistics(series)

    if "error" in dist_stats:
        raise HTTPException(status_code=400, detail=dist_stats["error"])

    return DistributionResponse(
        metric_name=metric_name,
        statistics=dist_stats,
        sample_confidence=dist_stats.get("sample_confidence", "UNKNOWN"),
    )


@router.get("/correlations", response_model=CorrelationResponse)
def get_correlations(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Get correlation analysis between behavioral metrics."""
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)

    # Merge data for correlation analysis
    merged = sessions_df.merge(tasks_df[["id", "category", "priority", "status"]], 
                               left_on="task_id", right_on="id", how="left")

    # Select numeric columns for correlation
    numeric_cols = ["focused_time_seconds", "interruption_time_seconds", 
                    "context_switch_count", "interruption_count"]
    available_cols = [col for col in numeric_cols if col in merged.columns]

    if len(available_cols) < 2:
        raise HTTPException(status_code=400, detail="Insufficient numeric columns for correlation")

    corr_result = sa.compute_correlation_matrix(merged, available_cols)

    if "error" in corr_result:
        raise HTTPException(status_code=400, detail=corr_result["error"])

    return CorrelationResponse(**corr_result)


@router.get("/story", response_model=StoryAnalyticsResponse)
def get_story_analytics(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """
    Get story-driven analytics that tells a narrative about behavior.
    Follows the pattern: Behaviour → Pattern → Evidence → Risk → Recommendation
    """
    _require_user(db, user_id)
    since = _since(period_days)

    tasks_df = m.load_tasks_df(db, user_id, since=since)
    sessions_df = m.load_sessions_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    # Generate insights
    all_insights = ins.generate_all_insights(tasks_df, sessions_df, interruptions_df, location_labels)

    # Build narrative from insights
    high_risk_insights = [i for i in all_insights if i.get("risk_level") == "HIGH"]
    medium_risk_insights = [i for i in all_insights if i.get("risk_level") == "MEDIUM"]

    # Construct narrative
    if high_risk_insights:
        narrative = f"Your behavior analysis reveals {len(high_risk_insights)} high-risk patterns requiring attention. "
    else:
        narrative = "Your behavior patterns are relatively stable with no critical risks identified. "

    # Add key behaviors
    key_behaviors = []
    for insight in all_insights[:3]:
        if "message" in insight and "error" not in insight:
            key_behaviors.append(insight["message"])

    # Extract patterns
    patterns = [i["insight_type"] for i in all_insights if "error" not in i]

    # Extract risks
    risks = [i["message"] for i in high_risk_insights]

    # Extract recommendations
    recommendations = [i["recommendation"] for i in all_insights if "error" not in i]

    # Evidence traceability
    evidence = []
    for insight in all_insights[:5]:
        if "evidence" in insight and "error" not in insight:
            evidence.append({
                "insight_type": insight["insight_type"],
                "evidence": insight["evidence"],
            })

    # Data traceability
    data_traceability = {
        "tasks_count": len(tasks_df),
        "sessions_count": len(sessions_df),
        "interruptions_count": len(interruptions_df),
        "period_days": period_days,
        "data_source": "tasks, sessions, interruptions tables",
    }

    return StoryAnalyticsResponse(
        user_id=str(user_id),
        period_days=period_days,
        narrative=narrative,
        key_behaviors=key_behaviors,
        patterns=patterns,
        evidence=evidence,
        risks=risks,
        recommendations=recommendations[:3],  # Top 3 recommendations
        data_traceability=data_traceability,
    )


@router.get("/context-switch-timeline", response_model=ContextSwitchTimelineResponse)
def get_context_switch_timeline(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)

    events_df = m.load_events_df(db, user_id, since=since)
    tasks_df = m.load_tasks_df(db, user_id, since=since)
    interruptions_df = m.load_interruptions_df(db, user_id, since=since)
    location_labels = m.load_location_labels(db, user_id)

    timeline = []
    if not events_df.empty:
        events_sorted = events_df.sort_values("event_time")

        tasks_lookup = {}
        if not tasks_df.empty:
            tasks_lookup = {
                str(row["id"]): {
                    "title": row["title"],
                    "context_tag": row.get("category") or None,
                }
                for _, row in tasks_df.iterrows()
            }

        interr_windows = []
        if not interruptions_df.empty:
            for _, irow in interruptions_df.iterrows():
                start = irow["start_time"]
                duration_sec = irow["duration_seconds"] or 0
                end = start + timedelta(seconds=duration_sec)
                interr_windows.append((start, end))

        for _, erow in events_sorted.iterrows():
            event_time = erow["event_time"]
            task_id_str = str(erow["task_id"])
            task_info = tasks_lookup.get(task_id_str, {"title": "", "context_tag": None})

            event_loc_id = erow.get("location_id")
            loc_id_str = str(event_loc_id) if pd.notna(event_loc_id) and event_loc_id is not None else None

            is_interruption = False
            for win_start, win_end in interr_windows:
                if win_start <= event_time <= win_end:
                    is_interruption = True
                    break

            timeline.append({
                "timestamp": event_time.isoformat(),
                "task_id": task_id_str,
                "task_title": task_info["title"],
                "location_id": loc_id_str,
                "location_label": location_labels.get(event_loc_id, None) if loc_id_str else None,
                "context_tag": task_info["context_tag"],
                "event_type": str(erow["event_type"]),
                "is_interruption": is_interruption,
            })

    return ContextSwitchTimelineResponse(
        user_id=str(user_id),
        period_days=period_days,
        timeline=timeline,
    )


@router.get("/task-context-heatmap", response_model=TaskContextHeatmapResponse)
def get_task_context_heatmap(
    user_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=3650),
    value_metric: str = Query("completion_rate", pattern="^(completion_rate|forget_rate)$"),
    db: Session = Depends(get_db),
):
    _require_user(db, user_id)
    since = _since(period_days)
    tasks_df = m.load_tasks_df(db, user_id, since=since)

    columns = ["00-03", "04-07", "08-11", "12-15", "16-19", "20-23"]

    if tasks_df.empty:
        return TaskContextHeatmapResponse(
            user_id=str(user_id),
            period_days=period_days,
            metric=value_metric,
            rows=[],
            columns=columns,
            cells=[],
            sample_sizes=[],
        )

    context_tags = sorted([
        t for t in tasks_df["category"].dropna().unique().tolist()
        if t is not None and str(t).strip() != ""
    ])

    cells: list[list[float | None]] = []
    sample_sizes: list[list[int]] = []

    for tag in context_tags:
        tag_tasks = tasks_df[tasks_df["category"] == tag].copy()
        row_vals: list[float | None] = []
        row_sizes: list[int] = []

        for bucket_idx in range(6):
            bucket_mask = (tag_tasks["created_at"].dt.hour // 4) == bucket_idx
            bucket = tag_tasks[bucket_mask]
            total = len(bucket)
            row_sizes.append(total)

            if total < 3:
                row_vals.append(None)
                continue

            if value_metric == "completion_rate":
                completed = len(bucket[bucket["status"] == "completed"])
                rate = round(completed / total, 4)
            else:
                resolved = bucket[bucket["status"].isin(["completed", "forgotten", "cancelled"])]
                total_resolved = len(resolved)
                if total_resolved == 0:
                    row_vals.append(None)
                    continue
                forgotten = len(resolved[resolved["status"] == "forgotten"])
                rate = round(forgotten / total_resolved, 4)

            row_vals.append(rate)

        cells.append(row_vals)
        sample_sizes.append(row_sizes)

    return TaskContextHeatmapResponse(
        user_id=str(user_id),
        period_days=period_days,
        metric=value_metric,
        rows=context_tags,
        columns=columns,
        cells=cells,
        sample_sizes=sample_sizes,
    )
