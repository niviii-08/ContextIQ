"""
Stage 5 — Batch Feature Engineering
=====================================

Generates the complete ML-ready feature matrix for every task in the
dataset. Each row in the output represents a single task with all features
computed strictly BEFORE that task''s created_at timestamp (leakage-free).

Feature groups
--------------
A. Task-level (from existing app/utils/features.py — preserved & extended)
   - previous_forgetting_count     : # tasks forgotten before this one
   - previous_completion_count     : # tasks completed before this one
   - completion_rate               : historical completion rate
   - category_forgetting_rate      : forgetting rate for same category
   - location_forgetting_rate      : forgetting rate at same location
   - weekday_forgetting_rate       : forgetting rate on same weekday
   - hour_forgetting_rate          : forgetting rate at same hour-of-day
   - task_frequency                : # same-category tasks before this one
   - days_since_last_similar       : days since last same-category task
   - deadline_distance_hours       : hours between creation and deadline
   - priority                      : task priority (1–5)
   - tasks_today                   : # tasks created in the last 24 h
   - interruptions_today           : # interruptions in the last 24 h
   - recent_context_switches       : paused→resumed count in last 24 h
   - avg_interruption_duration_s   : mean interruption duration (all history)

B. Extended features (new in this module)
   - recovery_time_s               : mean PAUSED→RESUMED gap for this user
   - daily_friction_score          : rolling 7-day weighted friction score
   - repeated_context_count        : # prior tasks in same category+location
   - forgetting_streak             : consecutive forgotten tasks immediately
                                     before this one
   - avg_session_duration_7d_s     : mean session duration in last 7 days
   - context_switch_rate_7d        : context_switches per session in last 7 d
   - is_late_night                 : created_at.hour >= 21
   - is_repeated_context           : user has done this ctx pair before
   - task_location_pair            : "<category>@<location_type>" key

C. Target variable
   - will_forget                   : 1 if task status == "forgotten", else 0

LEAKAGE PREVENTION
------------------
Every feature is computed with:
    data filtered to timestamps STRICTLY BEFORE task.created_at
This is enforced by the _before() helper (same pattern as app/utils/features.py).
The target column (will_forget) is derived from the task''s OWN final status,
which is the thing being predicted — this is correct and not leakage.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── leakage-prevention helper ─────────────────────────────────────────────────

def _ensure_utc_aware(dt) -> datetime:
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _before(df: pd.DataFrame, col: str, as_of: datetime) -> pd.DataFrame:
    """Filter df to rows where df[col] < as_of (strict). Handles tz mismatch."""
    if df.empty or col not in df.columns:
        return df
    series = df[col]
    col_tz_aware = getattr(series.dt, "tz", None) is not None if pd.api.types.is_datetime64_any_dtype(series) else False
    as_of_aware = as_of.tzinfo is not None
    if col_tz_aware and not as_of_aware:
        as_of = as_of.replace(tzinfo=timezone.utc)
    elif not col_tz_aware and as_of_aware:
        as_of = as_of.replace(tzinfo=None)
    return df[series < as_of]


def _last_n_days(df: pd.DataFrame, col: str, as_of: datetime, days: int) -> pd.DataFrame:
    hist = _before(df, col, as_of)
    if hist.empty:
        return hist
    cutoff = as_of - timedelta(days=days)
    series = hist[col]
    col_tz_aware = getattr(series.dt, "tz", None) is not None if pd.api.types.is_datetime64_any_dtype(series) else False
    if col_tz_aware and cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    elif not col_tz_aware and cutoff.tzinfo is not None:
        cutoff = cutoff.replace(tzinfo=None)
    return hist[series >= cutoff]


# ── per-task feature helpers ──────────────────────────────────────────────────

def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _forgetting_streak(tasks_hist: pd.DataFrame) -> int:
    """Number of consecutive forgotten tasks immediately before as_of."""
    if tasks_hist.empty or "status" not in tasks_hist.columns:
        return 0
    ordered = tasks_hist.sort_values("created_at")["status"].tolist()
    streak = 0
    for s in reversed(ordered):
        if s == "forgotten":
            streak += 1
        else:
            break
    return streak


def _recovery_time_s(events_hist: pd.DataFrame) -> float | None:
    """Mean gap (seconds) between paused and next resumed event for this user."""
    if events_hist.empty:
        return None
    paused = events_hist[events_hist["event_type"] == "paused"].sort_values("event_time")
    resumed = events_hist[events_hist["event_type"] == "resumed"].sort_values("event_time")
    if paused.empty or resumed.empty:
        return None

    gaps = []
    for _, pause_row in paused.iterrows():
        pause_time = pause_row["event_time"]
        # find next resume after this pause for the same task
        task_resumes = resumed[
            (resumed["task_id"] == pause_row["task_id"]) &
            (resumed["event_time"] > pause_time)
        ]
        if not task_resumes.empty:
            resume_time = task_resumes["event_time"].min()
            gap = (resume_time - pause_time).total_seconds()
            if gap >= 0:
                gaps.append(gap)

    return round(float(np.mean(gaps)), 2) if gaps else None


def _daily_friction(tasks_hist: pd.DataFrame, interruptions_hist: pd.DataFrame, sessions_hist: pd.DataFrame) -> float | None:
    """Rolling 7-day friction: weighted combination of forgetting and interruption rate."""
    if tasks_hist.empty:
        return None
    resolved = tasks_hist[tasks_hist["status"].isin(["completed", "forgotten", "cancelled"])]
    if resolved.empty:
        return None
    forget_rate = (resolved["status"] == "forgotten").sum() / len(resolved)
    n_interruptions = len(interruptions_hist)
    n_sessions = len(sessions_hist)
    session_active_s = float(sessions_hist["focused_time_seconds"].sum()) if not sessions_hist.empty else 0
    active_h = session_active_s / 3600.0
    interruption_rate = (n_interruptions / active_h) if active_h > 0 else 0
    # Normalize: assume saturation at 6 interruptions/h
    interruption_norm = min(1.0, interruption_rate / 6.0)
    return round(0.6 * float(forget_rate) + 0.4 * interruption_norm, 4)


def _context_switch_rate_7d(sessions_hist: pd.DataFrame) -> float | None:
    """Mean context switches per session in last 7 days."""
    if sessions_hist.empty or "context_switch_count" not in sessions_hist.columns:
        return None
    return round(float(sessions_hist["context_switch_count"].mean()), 4)


def _avg_session_duration_7d_s(sessions_hist: pd.DataFrame) -> float | None:
    """Mean focused session duration in last 7 days, in seconds."""
    if sessions_hist.empty or "focused_time_seconds" not in sessions_hist.columns:
        return None
    return round(float(sessions_hist["focused_time_seconds"].mean()), 2)


def _repeated_context_count(tasks_hist: pd.DataFrame, category: str, location_id) -> int:
    """How many prior tasks share the same (category, location_id) pair."""
    if tasks_hist.empty:
        return 0
    mask = tasks_hist["category"] == category
    if location_id is not None and "location_id" in tasks_hist.columns:
        mask = mask & (tasks_hist["location_id"] == location_id)
    return int(mask.sum())


# ── main batch feature generator ─────────────────────────────────────────────

def generate_feature_matrix(
    tasks_df: pd.DataFrame,
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    locations_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Build the ML-ready feature matrix for every task.

    Parameters
    ----------
    tasks_df        : Cleaned + transformed tasks (must have: id, user_id,
                      category, status, created_at, priority, location_id)
    events_df       : Cleaned + transformed task_events
    interruptions_df: Cleaned interruptions
    sessions_df     : Reconstructed sessions (from pipeline/reconstruct.py)
    locations_df    : Optional locations table for location_type lookup

    Returns
    -------
    pd.DataFrame
        One row per task, with all features + target column `will_forget`.
    """
    if tasks_df.empty:
        logger.warning("generate_feature_matrix: tasks_df is empty")
        return pd.DataFrame()

    loc_type_map: dict = {}
    if locations_df is not None and not locations_df.empty:
        if "id" in locations_df.columns and "location_type" in locations_df.columns:
            loc_type_map = locations_df.set_index("id")["location_type"].to_dict()

    tasks_sorted = tasks_df.sort_values(["user_id", "created_at"]).reset_index(drop=True) if "user_id" in tasks_df.columns and "created_at" in tasks_df.columns else tasks_df.copy().reset_index(drop=True)

    tasks_by_user: dict[Any, pd.DataFrame] = {}
    events_by_user: dict[Any, pd.DataFrame] = {}
    ints_by_user: dict[Any, pd.DataFrame] = {}
    sessions_by_user: dict[Any, pd.DataFrame] = {}

    has_user = "user_id" in tasks_sorted.columns
    if has_user:
        for uid, grp in tasks_sorted.groupby("user_id", sort=False):
            tasks_by_user[uid] = grp.sort_values("created_at").reset_index(drop=True)
        if not events_df.empty and "user_id" in events_df.columns:
            for uid, grp in events_df.groupby("user_id", sort=False):
                events_by_user[uid] = grp.sort_values("event_time").reset_index(drop=True)
        if not interruptions_df.empty and "user_id" in interruptions_df.columns:
            for uid, grp in interruptions_df.groupby("user_id", sort=False):
                ints_by_user[uid] = grp.sort_values("start_time").reset_index(drop=True)
        if not sessions_df.empty and "user_id" in sessions_df.columns:
            for uid, grp in sessions_df.groupby("user_id", sort=False):
                sessions_by_user[uid] = grp.sort_values("session_start").reset_index(drop=True)
    else:
        tasks_by_user["_all"] = tasks_sorted
        events_by_user["_all"] = events_df
        ints_by_user["_all"] = interruptions_df
        sessions_by_user["_all"] = sessions_df

    rows: list[dict] = []
    total = len(tasks_sorted)
    processed = 0

    for user_id, user_tasks in tasks_by_user.items():
        user_events = events_by_user.get(user_id, pd.DataFrame())
        user_interruptions = ints_by_user.get(user_id, pd.DataFrame())
        user_sessions = sessions_by_user.get(user_id, pd.DataFrame())

        has_et = "event_time" in user_events.columns and not user_events.empty
        has_st = "start_time" in user_interruptions.columns and not user_interruptions.empty
        has_ss = "session_start" in user_sessions.columns and not user_sessions.empty

        et_vals = pd.to_datetime(user_events["event_time"], utc=True) if has_et else None
        st_vals = pd.to_datetime(user_interruptions["start_time"], utc=True) if has_st else None
        ss_vals = pd.to_datetime(user_sessions["session_start"], utc=True) if has_ss else None
        task_ct_vals = pd.to_datetime(user_tasks["created_at"], utc=True)

        status_arr = user_tasks["status"].to_numpy() if "status" in user_tasks.columns else None
        category_arr = user_tasks["category"].to_numpy() if "category" in user_tasks.columns else None
        location_arr = user_tasks["location_id"].to_numpy() if "location_id" in user_tasks.columns else None
        priority_arr = user_tasks["priority"].to_numpy() if "priority" in user_tasks.columns else None
        deadline_arr = user_tasks["deadline_at"].to_numpy() if "deadline_at" in user_tasks.columns else None
        id_arr = user_tasks["id"].to_numpy() if "id" in user_tasks.columns else None
        uid_arr = user_tasks["user_id"].to_numpy() if has_user and "user_id" in user_tasks.columns else None

        n_user_tasks = len(user_tasks)
        for j in range(n_user_tasks):
            as_of_raw = task_ct_vals.iloc[j]
            if pd.isna(as_of_raw):
                processed += 1
                continue
            if isinstance(as_of_raw, pd.Timestamp):
                as_of = as_of_raw.to_pydatetime()
            else:
                as_of = as_of_raw
            if as_of.tzinfo is None:
                as_of = as_of.replace(tzinfo=timezone.utc)

            category = "" if category_arr is None else str(category_arr[j])
            location_id = None if location_arr is None else location_arr[j]
            priority = 3 if priority_arr is None else priority_arr[j]
            deadline_at = None if deadline_arr is None else deadline_arr[j]
            Status = "" if status_arr is None else str(status_arr[j])
            status_low = Status.lower()
            task_id = None if id_arr is None else id_arr[j]
            task_uid = None if uid_arr is None else uid_arr[j]

            tasks_hist = user_tasks.iloc[:j]
            if not tasks_hist.empty:
                hist_ct = task_ct_vals.iloc[:j]
                mask_before = hist_ct < as_of
                tasks_hist = tasks_hist[mask_before.values]

            events_hist = pd.DataFrame()
            if has_et:
                mask_ev = et_vals < as_of
                events_hist = user_events.iloc[mask_ev.values]

            interruptions_hist = pd.DataFrame()
            if has_st:
                mask_int = st_vals < as_of
                interruptions_hist = user_interruptions.iloc[mask_int.values]

            sessions_hist = pd.DataFrame()
            if has_ss:
                mask_ss = ss_vals < as_of
                sessions_hist = user_sessions.iloc[mask_ss.values]

            cutoff_7d = as_of - timedelta(days=7)
            cutoff_1d = as_of - timedelta(days=1)

            tasks_7d = pd.DataFrame()
            if not tasks_hist.empty:
                hist_ct_7 = pd.to_datetime(tasks_hist["created_at"], utc=True)
                tasks_7d = tasks_hist.iloc[(hist_ct_7 >= cutoff_7d).values]

            events_7d = pd.DataFrame()
            if has_et:
                mask_ev_7 = (et_vals >= cutoff_7d) & (et_vals < as_of)
                events_7d = user_events.iloc[mask_ev_7.values]

            interruptions_7d = pd.DataFrame()
            if has_st:
                mask_int_7 = (st_vals >= cutoff_7d) & (st_vals < as_of)
                interruptions_7d = user_interruptions.iloc[mask_int_7.values]

            sessions_7d = pd.DataFrame()
            if has_ss:
                mask_ss_7 = (ss_vals >= cutoff_7d) & (ss_vals < as_of)
                sessions_7d = user_sessions.iloc[mask_ss_7.values]

            interruptions_24h = pd.DataFrame()
            if has_st:
                mask_int_24 = (st_vals >= cutoff_1d) & (st_vals < as_of)
                interruptions_24h = user_interruptions.iloc[mask_int_24.values]

            tasks_24h = pd.DataFrame()
            if not tasks_hist.empty:
                hist_ct_24 = pd.to_datetime(tasks_hist["created_at"], utc=True)
                tasks_24h = tasks_hist.iloc[(hist_ct_24 >= cutoff_1d).values]

            resolved = pd.DataFrame()
            cat_resolved = pd.DataFrame()
            loc_resolved = pd.DataFrame()
            if not tasks_hist.empty:
                status_col = tasks_hist["status"].to_numpy()
                resolved_mask = np.isin(status_col, ["completed", "forgotten", "cancelled"])
                resolved = tasks_hist.iloc[resolved_mask]
                if not resolved.empty:
                    cat_col = resolved["category"].to_numpy()
                    cat_resolved = resolved.iloc[cat_col == category]
                    if location_id is not None and "location_id" in resolved.columns:
                        loc_col = resolved["location_id"].to_numpy()
                        loc_resolved = resolved.iloc[loc_col == location_id]

            weekday = as_of.strftime("%A")
            hour = as_of.hour

            def wd_forget_rate(hist: pd.DataFrame) -> float | None:
                if hist.empty or "created_at" not in hist.columns:
                    return None
                wd = pd.to_datetime(hist["created_at"], utc=True).dt.day_name().to_numpy()
                subset = hist.iloc[wd == weekday]
                if subset.empty:
                    return None
                return _safe_rate(int((subset["status"].to_numpy() == "forgotten").sum()), len(subset))

            def hr_forget_rate(hist: pd.DataFrame) -> float | None:
                if hist.empty or "created_at" not in hist.columns:
                    return None
                hr = pd.to_datetime(hist["created_at"], utc=True).dt.hour.to_numpy()
                subset = hist.iloc[hr == hour]
                if subset.empty:
                    return None
                return _safe_rate(int((subset["status"].to_numpy() == "forgotten").sum()), len(subset))

            deadline_dist_h = None
            if deadline_at is not None and not (isinstance(deadline_at, float) and np.isnan(deadline_at)):
                try:
                    dl = _ensure_utc_aware(deadline_at)
                    deadline_dist_h = round((dl - as_of).total_seconds() / 3600.0, 3)
                except Exception:
                    pass

            loc_type = loc_type_map.get(location_id, "UNKNOWN") if location_id is not None else "UNKNOWN"
            task_location_pair = f"{category}@{loc_type}"

            recent_ctx_switches = 0
            if not events_7d.empty and "event_type" in events_7d.columns:
                recent_ctx_switches = int((events_7d["event_type"].to_numpy() == "resumed").sum())

            avg_int_dur = None
            if not interruptions_hist.empty and "duration_seconds" in interruptions_hist.columns:
                vals = interruptions_hist["duration_seconds"].dropna()
                if not vals.empty:
                    avg_int_dur = round(float(vals.mean()), 2)

            days_since = None
            if not tasks_hist.empty and "category" in tasks_hist.columns:
                cat_col = tasks_hist["category"].to_numpy()
                matches = cat_col == category
                if matches.any():
                    subset_ct = pd.to_datetime(tasks_hist.iloc[matches]["created_at"], utc=True)
                    last_time = subset_ct.max()
                    try:
                        days_since = round((as_of - last_time.to_pydatetime().replace(tzinfo=timezone.utc)).total_seconds() / 86400.0, 3)
                    except Exception:
                        days_since = round((as_of - last_time).total_seconds() / 86400.0, 3)

            resolved_statuses = resolved["status"].to_numpy() if not resolved.empty else np.array([])
            cat_res_statuses = cat_resolved["status"].to_numpy() if not cat_resolved.empty else np.array([])
            loc_res_statuses = loc_resolved["status"].to_numpy() if not loc_resolved.empty else np.array([])
            tasks_hist_statuses = tasks_hist["status"].to_numpy() if not tasks_hist.empty else np.array([])
            tasks_hist_categories = tasks_hist["category"].to_numpy() if not tasks_hist.empty and "category" in tasks_hist.columns else np.array([])

            feat = {
                "task_id": task_id,
                "user_id": user_id if has_user and user_id != "_all" else task_uid,
                "created_at": task_ct_vals.iloc[j],
                "status": status_low,
                "previous_forgetting_count": int((tasks_hist_statuses == "forgotten").sum()) if len(tasks_hist_statuses) else 0,
                "previous_completion_count": int((tasks_hist_statuses == "completed").sum()) if len(tasks_hist_statuses) else 0,
                "completion_rate": _safe_rate(int((resolved_statuses == "completed").sum()), len(resolved_statuses)) if len(resolved_statuses) else None,
                "category_forgetting_rate": _safe_rate(int((cat_res_statuses == "forgotten").sum()), len(cat_res_statuses)) if len(cat_res_statuses) else None,
                "location_forgetting_rate": _safe_rate(int((loc_res_statuses == "forgotten").sum()), len(loc_res_statuses)) if len(loc_res_statuses) else None,
                "weekday_forgetting_rate": wd_forget_rate(resolved),
                "hour_forgetting_rate": hr_forget_rate(resolved),
                "task_frequency": int((tasks_hist_categories == category).sum()) if len(tasks_hist_categories) else 0,
                "days_since_last_similar": days_since,
                "deadline_distance_hours": deadline_dist_h,
                "priority": int(priority) if priority is not None else 3,
                "tasks_today": len(tasks_24h),
                "interruptions_today": len(interruptions_24h),
                "recent_context_switches": recent_ctx_switches,
                "avg_interruption_duration_s": avg_int_dur,
                "recovery_time_s": _recovery_time_s(events_hist),
                "daily_friction_score": _daily_friction(tasks_7d, interruptions_7d, sessions_7d),
                "repeated_context_count": _repeated_context_count(tasks_hist, category, location_id),
                "forgetting_streak": _forgetting_streak(tasks_hist),
                "avg_session_duration_7d_s": _avg_session_duration_7d_s(sessions_7d),
                "context_switch_rate_7d": _context_switch_rate_7d(sessions_7d),
                "is_late_night": int(hour >= 21),
                "is_repeated_context": int(_repeated_context_count(tasks_hist, category, location_id) > 0),
                "task_location_pair": task_location_pair,
                "will_forget": int(status_low == "forgotten"),
            }
            rows.append(feat)
            processed += 1

            if processed % 1000 == 0 or processed == total:
                logger.info("generate_feature_matrix: processed %d/%d tasks", processed, total)

    if not rows:
        return pd.DataFrame()

    feature_df = pd.DataFrame(rows)
    logger.info(
        "generate_feature_matrix: produced %d rows x %d features (target: will_forget, class balance: %.1f%% positive)",
        len(feature_df), feature_df.shape[1],
        100.0 * feature_df["will_forget"].mean() if "will_forget" in feature_df.columns else 0,
    )
    return feature_df
