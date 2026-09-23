"""
generate_dataset.py

Generates a synthetic, reproducible behavioural dataset simulating task
completion / forgetting patterns for ContextIQ users.

DESIGN GOALS
------------
1. Realistic correlations: forgetting probability is driven by a weighted
   combination of ~12 behavioural signals, each with a plausible real-world
   relationship to forgetting (e.g. more interruptions -> more forgetting,
   higher historical completion rate -> less forgetting).
2. No single trivially-determining feature: no one feature has enough
   weight to determine the label on its own. Weights are distributed across
   many signals and noise is injected.
3. Reproducibility: a fixed numpy random seed is used throughout.
4. Temporal validity: each row is a "prediction point" — a task instance
   that occurs at a specific timestamp. Every feature attached to a row is
   computable using ONLY information strictly prior to that timestamp.
   The label ("forgotten") is the actual outcome of THAT task instance,
   which is only known after the task's deadline/window has passed - i.e.
   it is not used as a feature for itself or for any other row.

OUTPUT
------
datasets/tasks_raw.csv       - one row per task observation (prediction point)
datasets/users.csv           - static-ish per-user reference table
datasets/dataset_metadata.json - reproducibility & leakage proof metadata
"""

import hashlib
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from ml.training.config import SEED, DATASET_CONFIG, DATASET_VERSION

OUT_DIR = Path(__file__).resolve().parents[2] / "datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["Academic", "Work", "Personal", "Health", "Household", "Social", "Finance"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH"]
LOCATIONS = ["Home", "Campus", "Office", "Commute", "Gym", "Other"]

CATEGORY_BASE_FORGET_RATE = {
    "Academic": 0.20,
    "Work": 0.15,
    "Personal": 0.30,
    "Health": 0.22,
    "Household": 0.35,
    "Social": 0.28,
    "Finance": 0.18,
}

PRIORITY_EFFECT = {"LOW": 0.10, "MEDIUM": 0.0, "HIGH": -0.12}


def sample_user_archetypes(n_users: int) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    user_ids = np.arange(1, n_users + 1)
    forgetfulness_trait = rng.beta(2.2, 5.0, size=n_users)
    organisation_trait = rng.beta(3.0, 3.0, size=n_users)
    daily_task_load_mean = rng.integers(2, 9, size=n_users)
    interruption_mean = rng.gamma(2.0, 1.3, size=n_users)
    session_duration_mean = rng.normal(35, 12, size=n_users).clip(5, 90)

    return pd.DataFrame({
        "user_id": user_ids,
        "forgetfulness_trait": forgetfulness_trait,
        "organisation_trait": organisation_trait,
        "daily_task_load_mean": daily_task_load_mean,
        "interruption_mean": interruption_mean,
        "session_duration_mean": session_duration_mean,
    })


def generate_events(users: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n_days = DATASET_CONFIG["n_days"]
    start_date = datetime(2025, 1, 1)
    rows = []

    for _, u in users.iterrows():
        user_id = int(u.user_id)
        forget_trait = u.forgetfulness_trait
        org_trait = u.organisation_trait
        load_mean = u.daily_task_load_mean
        interrupt_mean = u.interruption_mean
        session_mean = u.session_duration_mean

        completions = 0
        forgettings = 0
        total_tasks_seen = 0

        cat_completions = {c: 0 for c in CATEGORIES}
        cat_forgettings = {c: 0 for c in CATEGORIES}
        cat_seen = {c: 0 for c in CATEGORIES}

        for day_offset in range(n_days):
            current_date = start_date + timedelta(days=day_offset)
            weekday = current_date.weekday()

            n_tasks_today = max(0, int(rng.poisson(load_mean)))
            if n_tasks_today == 0:
                continue

            interruptions_today_total = max(0, int(rng.poisson(interrupt_mean)))
            avg_interruption_duration = float(rng.gamma(2.0, 4.0) + 1.0)
            avg_session_duration = float(np.clip(rng.normal(session_mean, 8), 5, 120))

            recent_context_switches = max(0, int(rng.poisson(interrupt_mean * 1.4)))

            pending_tasks = []
            for t in range(n_tasks_today):
                category = rng.choice(CATEGORIES)
                priority = rng.choice(PRIORITIES, p=[0.35, 0.40, 0.25])
                location = rng.choice(LOCATIONS)
                hour = int(rng.integers(6, 23))
                deadline_distance_hours = float(rng.gamma(2.0, 10.0) + 1.0)
                pending_tasks.append({
                    "t": t,
                    "category": category,
                    "priority": priority,
                    "location": location,
                    "hour": hour,
                    "deadline_distance_hours": deadline_distance_hours,
                })

            pending_tasks.sort(key=lambda x: (x["hour"], x["t"]))

            for order_idx, task in enumerate(pending_tasks):
                t = task["t"]
                category = task["category"]
                priority = task["priority"]
                location = task["location"]
                hour = task["hour"]
                deadline_distance_hours = task["deadline_distance_hours"]

                task_frequency = cat_seen[category] / max(1, total_tasks_seen)

                historical_completion_rate = (
                    completions / total_tasks_seen if total_tasks_seen > 0 else 0.5
                )
                historical_forgetting_rate = (
                    forgettings / total_tasks_seen if total_tasks_seen > 0 else 0.5
                )
                previous_completion_count = completions
                previous_forgetting_count = forgettings

                interruptions_today = int(
                    round(interruptions_today_total * ((order_idx + 1) / n_tasks_today))
                )

                score = 0.0
                score += 1.8 * (forget_trait - 0.3)
                score += -1.4 * (org_trait - 0.5)
                score += (CATEGORY_BASE_FORGET_RATE[category] - 0.23) * 2.0
                score += PRIORITY_EFFECT[priority] * 1.5
                score += -0.9 * (historical_completion_rate - 0.5)
                score += 1.1 * (historical_forgetting_rate - 0.3)
                score += -0.35 * np.tanh(deadline_distance_hours / 24.0 - 0.5)
                score += 0.28 * np.tanh(interruptions_today / 5.0)
                score += 0.22 * np.tanh(recent_context_switches / 6.0)
                score += 0.15 * np.tanh(avg_interruption_duration / 10.0)
                score += -0.12 * np.tanh(avg_session_duration / 40.0)
                score += 0.10 * np.tanh(task_frequency * 3.0)
                if weekday >= 5 and category in ("Personal", "Household", "Social"):
                    score += 0.18
                if location in ("Commute", "Other"):
                    score += 0.10
                elif location == "Office":
                    score -= 0.08

                score += -1.1
                score += rng.normal(0, 0.55)

                prob_forget = 1.0 / (1.0 + np.exp(-score))
                forgotten = int(rng.random() < prob_forget)

                rows.append({
                    "task_id": f"U{user_id:03d}-D{day_offset:03d}-T{t:02d}",
                    "user_id": user_id,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "weekday": weekday,
                    "hour": hour,
                    "task_category": category,
                    "priority": priority,
                    "location": location,
                    "deadline_distance_hours": round(deadline_distance_hours, 2),
                    "previous_completion_count": previous_completion_count,
                    "previous_forgetting_count": previous_forgetting_count,
                    "historical_completion_rate": round(historical_completion_rate, 4),
                    "historical_forgetting_rate": round(historical_forgetting_rate, 4),
                    "task_frequency": round(task_frequency, 4),
                    "tasks_today": n_tasks_today,
                    "interruptions_today": interruptions_today,
                    "recent_context_switches": recent_context_switches,
                    "avg_interruption_duration": round(avg_interruption_duration, 2),
                    "avg_session_duration": round(avg_session_duration, 2),
                    "forgotten": forgotten,
                })

                total_tasks_seen += 1
                cat_seen[category] += 1
                if forgotten:
                    forgettings += 1
                    cat_forgettings[category] += 1
                else:
                    completions += 1
                    cat_completions[category] += 1

    df = pd.DataFrame(rows)
    df = df.sort_values(["date", "user_id", "hour"]).reset_index(drop=True)
    return df


def _assert_no_target_leakage(df: pd.DataFrame) -> None:
    for uid, group in df.groupby("user_id"):
        g = group.sort_values(["date", "hour"]).reset_index(drop=True)
        if len(g) < 2:
            continue
        rolling_fg = 0
        rolling_cp = 0
        for i in range(len(g)):
            row = g.iloc[i]
            actual_pfc = int(row["previous_forgetting_count"])
            actual_pcc = int(row["previous_completion_count"])
            if i > 0:
                prev = g.iloc[i - 1]
                if int(prev["forgotten"]) == 1:
                    rolling_fg += 1
                else:
                    rolling_cp += 1
            assert actual_pfc == rolling_fg, (
                f"Leakage check failed user={uid} row i={i}: "
                f"previous_forgetting_count={actual_pfc} but should be {rolling_fg} "
                f"(prev[{i-1}].forgotten={int(prev['forgotten']) if i>0 else 'N/A'})"
            )
            assert actual_pcc == rolling_cp, (
                f"Leakage check failed user={uid} row i={i}: "
                f"previous_completion_count={actual_pcc} but should be {rolling_cp}"
            )
            if i > 0:
                n = float(i)
                expected_hfr = rolling_fg / n if n > 0 else 0.5
                expected_hcr = rolling_cp / n if n > 0 else 0.5
                actual_hfr = float(row["historical_forgetting_rate"])
                actual_hcr = float(row["historical_completion_rate"])
                assert abs(actual_hfr - expected_hfr) < 5e-3, (
                    f"Leakage check failed user={uid} row i={i}: "
                    f"historical_forgetting_rate={actual_hfr:.4f} vs expected {expected_hfr:.4f}"
                )
                assert abs(actual_hcr - expected_hcr) < 5e-3, (
                    f"Leakage check failed user={uid} row i={i}: "
                    f"historical_completion_rate={actual_hcr:.4f} vs expected {expected_hcr:.4f}"
                )


def _fingerprint_df(df: pd.DataFrame) -> str:
    cols = sorted(df.columns)
    h = hashlib.sha256()
    h.update(",".join(cols).encode())
    h.update(str(len(df)).encode())
    h.update(df[cols].head(100).to_csv(index=False).encode())
    return h.hexdigest()[:16]


def main():
    t0 = time.time()
    n_users = DATASET_CONFIG["n_users"]
    n_days = DATASET_CONFIG["n_days"]
    min_obs = DATASET_CONFIG["min_observations"]

    users = sample_user_archetypes(n_users)
    events = generate_events(users)

    if len(events) < min_obs:
        raise RuntimeError(
            f"Generated only {len(events)} rows, need >= {min_obs}. "
            "Increase N_DAYS or daily_task_load_mean range."
        )

    print("Running target-leakage assertions (first 5 users, full history)...")
    sample_for_leakage = events[events["user_id"].isin(events["user_id"].unique()[:5])]
    _assert_no_target_leakage(sample_for_leakage)
    print("Leakage checks passed.")

    events_path = OUT_DIR / "tasks_raw.csv"
    users_path = OUT_DIR / "users.csv"
    metadata_path = OUT_DIR / "dataset_metadata.json"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    events.to_csv(events_path, index=False)
    users.drop(columns=[]).to_csv(users_path, index=False)

    fingerprint = _fingerprint_df(events)
    date_range = (events["date"].min(), events["date"].max())
    class_dist = events["forgotten"].value_counts(normalize=True).to_dict()

    metadata = {
        "dataset_version": DATASET_VERSION,
        "seed": SEED,
        "config": DATASET_CONFIG,
        "generated_at_unix": time.time(),
        "n_rows": int(len(events)),
        "n_users": int(events["user_id"].nunique()),
        "n_unique_tasks": int(events["task_id"].nunique()),
        "date_range": list(date_range),
        "class_balance": {str(k): float(v) for k, v in class_dist.items()},
        "fingerprint_sha256_16": fingerprint,
        "leakage_check_sampled_users": 5,
        "leakage_check_status": "passed",
        "feature_columns": {
            "categorical": ["task_category", "priority", "location"],
            "numeric": [
                "weekday", "hour", "deadline_distance_hours",
                "previous_completion_count", "previous_forgetting_count",
                "historical_completion_rate", "historical_forgetting_rate",
                "task_frequency", "tasks_today", "interruptions_today",
                "recent_context_switches", "avg_interruption_duration",
                "avg_session_duration",
            ],
            "target": "forgotten",
        },
        "notes": (
            "Each row is a prediction point. All rolling historical features "
            "(previous_completion_count, historical_forgetting_rate, etc.) "
            "use ONLY information from strictly prior rows for that user; "
            "the current row's own 'forgotten' outcome is never included in "
            "its own features. Dataset is sorted chronologically globally "
            "(date, user_id, hour)."
        ),
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    elapsed = time.time() - t0
    print(f"Generated {len(events)} task observations across {n_users} users over {n_days} days in {elapsed:.1f}s.")
    print(f"Overall forgetting rate: {events['forgotten'].mean():.4f}")
    print(f"Fingerprint: {fingerprint}")
    print(f"Saved: {events_path}")
    print(f"Saved: {users_path}")
    print(f"Saved: {metadata_path}")


if __name__ == "__main__":
    main()
