"""
Stage 9 — Pipeline Orchestrator
================================

Single entrypoint that runs every stage of the ContextIQ data engineering
pipeline sequentially, with stage-level logging and timing.

Usage:
    python pipeline/run_pipeline.py --seed 42
    python pipeline/run_pipeline.py --users 50 --days 60 --seed 42
    python pipeline/run_pipeline.py --seed 42 --skip-training
    python pipeline/run_pipeline.py --seed 42 --csv-only
    python pipeline/run_pipeline.py --seed 42 --report-dir data/reports
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
DATA_ENGINE_ROOT = HERE.parents[1]
sys.path.insert(0, str(DATA_ENGINE_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-28s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_pipeline")


# ── stage helpers ─────────────────────────────────────────────────────────────

def _stage_header(name: str, stage_num: int) -> None:
    sep = "=" * 72
    logger.info("\n%s\n  STAGE %d — %s\n%s", sep, stage_num, name, sep)


def _stage_footer(name: str, elapsed_s: float) -> None:
    logger.info("  ✓ %s completed in %.1fs\n", name, elapsed_s)


# ── individual stages ────────────────────────────────────────────────────────

def stage_0_synthetic(args) -> dict[str, pd.DataFrame]:
    _stage_header("Synthetic Data Generation", 0)
    t0 = time.time()
    from scripts.generate_synthetic_data import SyntheticDataGenerator, write_csv

    gen = SyntheticDataGenerator(num_users=args.users, num_days=args.days, seed=args.seed)
    frames = gen.generate()

    total_events = len(frames["task_events"]) + len(frames["interruptions"])
    logger.info(
        "Generated: %d users, %d locations, %d tasks, %d task_events, %d interruptions",
        len(frames["users"]), len(frames["locations"]), len(frames["tasks"]),
        len(frames["task_events"]), len(frames["interruptions"]),
    )
    logger.info("Total raw behavioural events: %d", total_events)

    out_dir = DATA_ENGINE_ROOT / "data" / "synthetic"
    if args.csv_only:
        write_csv(frames, out_dir)
    _stage_footer("Synthetic Data Generation", time.time() - t0)
    return frames


def stage_1_validate(frames: dict[str, pd.DataFrame]):
    _stage_header("Data Validation", 1)
    t0 = time.time()
    from pipeline.validate import validate_all, ValidationReport

    report: ValidationReport = validate_all(
        frames["task_events"], frames["interruptions"], frames["tasks"],
    )
    logger.info(report.summary())
    if report.errors:
        logger.warning("  %d validation ERRORS found (data will still proceed, flagged for review)", len(report.errors))
    if report.warnings:
        logger.info("  %d validation warnings", len(report.warnings))
    _stage_footer("Data Validation", time.time() - t0)
    return report


def stage_2_clean(frames: dict[str, pd.DataFrame]):
    _stage_header("Data Cleaning", 2)
    t0 = time.time()
    from pipeline.clean import clean_all

    events_c, int_c, tasks_c, clean_report = clean_all(
        frames["task_events"], frames["interruptions"], frames["tasks"],
    )
    logger.info(clean_report.summary())
    frames_clean = dict(frames)
    frames_clean["task_events"] = events_c
    frames_clean["interruptions"] = int_c
    frames_clean["tasks"] = tasks_c
    _stage_footer("Data Cleaning", time.time() - t0)
    return frames_clean, clean_report


def stage_3_transform(frames: dict[str, pd.DataFrame]):
    _stage_header("Data Transformation", 3)
    t0 = time.time()
    from pipeline.transform import transform_all

    events_t, int_t, tasks_t = transform_all(
        frames["task_events"], frames["interruptions"], frames["tasks"],
        locations_df=frames.get("locations"),
    )
    frames_t = dict(frames)
    frames_t["task_events"] = events_t
    frames_t["interruptions"] = int_t
    frames_t["tasks"] = tasks_t
    logger.info(
        "Derived columns: events=%d cols, interruptions=%d cols, tasks=%d cols",
        events_t.shape[1], int_t.shape[1], tasks_t.shape[1],
    )
    _stage_footer("Data Transformation", time.time() - t0)
    return frames_t


def stage_4_reconstruct(frames: dict[str, pd.DataFrame]):
    _stage_header("Session Reconstruction", 4)
    t0 = time.time()
    from pipeline.reconstruct import reconstruct_sessions

    sessions_df = reconstruct_sessions(
        frames["task_events"], frames["interruptions"],
    )
    logger.info(
        "Reconstructed %d sessions (%d focused time hours total)",
        len(sessions_df),
        round(sessions_df["focused_time_seconds"].sum() / 3600.0, 1) if not sessions_df.empty else 0,
    )
    _stage_footer("Session Reconstruction", time.time() - t0)
    return sessions_df


def stage_5_features(frames: dict[str, pd.DataFrame], sessions_df: pd.DataFrame):
    _stage_header("Batch Feature Engineering", 5)
    t0 = time.time()
    from pipeline.features import generate_feature_matrix

    feature_df = generate_feature_matrix(
        frames["tasks"], frames["task_events"], frames["interruptions"],
        sessions_df, locations_df=frames.get("locations"),
    )
    if not feature_df.empty:
        target = feature_df["will_forget"].mean() * 100
        logger.info(
            "Feature matrix: %d rows x %d cols | target will_forget positive rate=%.1f%%",
            len(feature_df), feature_df.shape[1], target,
        )
    _stage_footer("Batch Feature Engineering", time.time() - t0)
    return feature_df


def stage_6_ml_export(feature_df: pd.DataFrame) -> dict:
    _stage_header("ML Dataset Export (Temporal Split)", 6)
    t0 = time.time()
    from pipeline.ml_export import export_ml_datasets

    ml_dir = DATA_ENGINE_ROOT / "data" / "ml"
    summary = export_ml_datasets(feature_df, output_dir=ml_dir, test_fraction=0.2)
    if summary:
        logger.info(
            "Train=%d | Test=%d | Features=%d | Split date=%s",
            summary.get("n_train"), summary.get("n_test"),
            summary.get("n_features"), summary.get("split_date", "N/A"),
        )
    _stage_footer("ML Dataset Export", time.time() - t0)
    return summary


def stage_7_model_training() -> dict | None:
    _stage_header("Model Training & Evaluation", 7)
    t0 = time.time()
    from pipeline.model import train_and_evaluate

    ml_dir = DATA_ENGINE_ROOT / "data" / "ml"
    models_dir = ml_dir / "models"
    report = train_and_evaluate(ml_dir=ml_dir, models_dir=models_dir)
    _stage_footer("Model Training & Evaluation", time.time() - t0)
    return report


def stage_8_populate_analytics(frames: dict[str, pd.DataFrame], sessions_df: pd.DataFrame) -> dict:
    _stage_header("Analytics Table Population", 8)
    t0 = time.time()
    from pipeline.populate_analytics import populate_analytics_tables

    result = populate_analytics_tables(
        frames["tasks"], frames["task_events"], frames["interruptions"],
        sessions_df, locations_df=frames.get("locations"),
    )
    logger.info(
        "behaviour_metrics rows inserted: daily=%d, category=%d, location=%d (total=%d)",
        result.get("daily_rows"), result.get("category_rows"),
        result.get("location_rows"), result.get("total_rows"),
    )
    _stage_footer("Analytics Table Population", time.time() - t0)
    return result


def stage_10_quality_report(
    frames: dict[str, pd.DataFrame],
    validation_report,
    clean_report,
    feature_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    args,
) -> str:
    _stage_header("Data Quality Report", 10)
    t0 = time.time()
    from pipeline.quality_report import generate_quality_report

    report_dir = Path(args.report_dir) if args.report_dir else DATA_ENGINE_ROOT / "data"
    report_paths = generate_quality_report(
        frames=frames,
        validation_report=validation_report,
        clean_report=clean_report,
        feature_df=feature_df,
        sessions_df=sessions_df,
        output_dir=report_dir,
    )
    logger.info("Quality report written to: %s", report_paths.get("markdown", "N/A"))
    logger.info("HTML report written to: %s", report_paths.get("html", "N/A"))
    _stage_footer("Data Quality Report", time.time() - t0)
    return report_paths.get("markdown", "")


# ── main orchestration ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ContextIQ Data Engineering Pipeline — End-to-End Orchestrator",
    )
    parser.add_argument("--users", type=int, default=50, help="Number of synthetic users (default: 50)")
    parser.add_argument("--days", type=int, default=60, help="Number of days of synthetic history (default: 60)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--skip-training", action="store_true", help="Skip Stage 7 model training")
    parser.add_argument("--csv-only", action="store_true", help="Only write CSVs, don't load into DB")
    parser.add_argument("--report-dir", type=str, default=None, help="Output directory for quality reports")
    args = parser.parse_args()

    pipeline_start = time.time()
    logger.info("╔══════════════════════════════════════════════════════════════════════════╗")
    logger.info("║  ContextIQ Data Engineering Pipeline                                     ║")
    logger.info("║  users=%d, days=%d, seed=%d, skip_training=%s                        ║",
                args.users, args.days, args.seed, args.skip_training)
    logger.info("╚══════════════════════════════════════════════════════════════════════════╝")

    frames = stage_0_synthetic(args)
    validation_report = stage_1_validate(frames)
    frames_clean, clean_report = stage_2_clean(frames)
    frames_t = stage_3_transform(frames_clean)
    sessions_df = stage_4_reconstruct(frames_t)
    feature_df = stage_5_features(frames_t, sessions_df)
    export_summary = stage_6_ml_export(feature_df)

    if not args.skip_training:
        model_report = stage_7_model_training()
    else:
        logger.info("  ⏭  Stage 7 (Model Training) skipped by --skip-training")
        model_report = None

    analytics_result = stage_8_populate_analytics(frames_t, sessions_df)
    quality_report_path = stage_10_quality_report(
        frames_t, validation_report, clean_report, feature_df, sessions_df, args,
    )

    elapsed_total = time.time() - pipeline_start
    sep = "=" * 72
    logger.info("\n%s\n  PIPELINE COMPLETE — total time: %.1fs\n%s", sep, elapsed_total, sep)
    logger.info("  Outputs:")
    logger.info("    data/synthetic/*.csv            → Raw CSVs (users, tasks, events, ...)")
    logger.info("    data/ml/train.parquet           → Training feature matrix")
    logger.info("    data/ml/test.parquet            → Test feature matrix")
    logger.info("    data/ml/feature_schema.json     → Feature column metadata")
    logger.info("    data/ml/models/*.joblib         → Trained model artifacts")
    logger.info("    data/ml/models/evaluation_report.json → Model metrics")
    logger.info("    data/quality_report.md          → Data quality report (Markdown)")
    logger.info("    contextiq.db [SQLite]           → behaviour_metrics table populated")
    logger.info("")

    if export_summary:
        logger.info("  ML Dataset Summary:")
        logger.info("    Train: %d rows (positive rate: %.1f%%)",
                    export_summary.get("n_train"), 100 * export_summary.get("train_positive_rate", 0))
        logger.info("    Test:  %d rows (positive rate: %.1f%%)",
                    export_summary.get("n_test"), 100 * export_summary.get("test_positive_rate", 0))
        logger.info("    Features: %d", export_summary.get("n_features"))

    if not args.skip_training and model_report and "models" in model_report:
        logger.info("\n  Model Evaluation:")
        for m in model_report["models"]:
            logger.info("    %-22s acc=%.4f  f1_w=%.4f  roc_auc=%s",
                        m["model"], m["accuracy"], m["f1_weighted"],
                        f"{m['roc_auc']:.4f}" if m.get("roc_auc") else "N/A")

    return 0


if __name__ == "__main__":
    sys.exit(main())
