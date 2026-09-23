"""
run_batch_prediction.py

Command-line utility for scoring a CSV of task observations using the
trained model, without going through the HTTP API. Useful for offline
batch scoring jobs, backfills, or CI smoke tests.

Usage:
    python scripts/run_batch_prediction.py --input path/to/tasks.csv --output path/to/predictions.csv

The input CSV must contain all raw feature columns defined in
ml/features/feature_spec.py (task_category, priority, location, weekday,
hour, deadline_distance_hours, previous_completion_count,
previous_forgetting_count, historical_completion_rate,
historical_forgetting_rate, task_frequency, tasks_today,
interruptions_today, recent_context_switches, avg_interruption_duration,
avg_session_duration). An optional `task_id` column is passed through.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.inference import ForgettingPredictor
from ml.features.feature_spec import DEFAULT_SPEC


def main():
    parser = argparse.ArgumentParser(description="Batch-score tasks for forgetting risk.")
    parser.add_argument("--input", required=True, help="Path to input CSV of task observations")
    parser.add_argument("--output", required=True, help="Path to write output CSV of predictions")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top contributing features to include")
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    required_cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Input CSV is missing required columns: {missing}")

    if "task_id" not in df.columns:
        df["task_id"] = [f"row_{i}" for i in range(len(df))]

    predictor = ForgettingPredictor.instance()
    tasks = df.to_dict(orient="records")
    predictions = predictor.predict_batch(tasks, top_k=args.top_k)

    out_df = pd.DataFrame(predictions)
    out_df["top_features"] = out_df["top_features"].apply(lambda r: " | ".join(r))
    out_df.to_csv(args.output, index=False)
    print(f"Scored {len(out_df)} tasks. Wrote predictions to {args.output}")


if __name__ == "__main__":
    main()
