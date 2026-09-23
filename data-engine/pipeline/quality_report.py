"""
Stage 10 — Data Quality Report Generator
==========================================

Generates both Markdown and HTML data quality reports covering:
  1. Record counts per table
  2. Null rates per column
  3. Event sequence validity
  4. Duplicate rates
  5. Timestamp range sanity
  6. Class balance for ML target
  7. Feature completeness

Outputs:
  data/quality_report.md   — human-readable Markdown
  data/quality_report.html — styled HTML version
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger(__name__)


# ── report section builders ──────────────────────────────────────────────────

def _table_counts_section(frames: dict[str, pd.DataFrame]) -> str:
    lines = ["## 1. Record Counts per Table\n", "| Table | Rows | Columns |", "|---|---:|---:|"]
    html_rows = ["<tr><th>Table</th><th>Rows</th><th>Columns</th></tr>"]
    for name, df in sorted(frames.items()):
        lines.append(f"| `{name}` | {len(df):,} | {df.shape[1]} |")
        html_rows.append(f"<tr><td><code>{html_escape(name)}</code></td><td>{len(df):,}</td><td>{df.shape[1]}</td></tr>")
    md = "\n".join(lines) + "\n"
    html = f"<h2>1. Record Counts per Table</h2>\n<table>{''.join(html_rows)}</table>\n"
    return md, html


def _null_rates_section(frames: dict[str, pd.DataFrame]) -> tuple[str, str]:
    md_lines = ["## 2. Null Rates per Column\n"]
    html_parts = ["<h2>2. Null Rates per Column</h2>"]
    for name, df in sorted(frames.items()):
        if df.empty:
            continue
        nulls = df.isna().mean()
        significant = nulls[nulls > 0.001]  # only show cols with >0.1% nulls
        if significant.empty:
            md_lines.append(f"\n### `{name}` — all columns fully populated (≤0.1% nulls)\n")
            html_parts.append(f"<h3><code>{html_escape(name)}</code> — all columns fully populated (≤0.1% nulls)</h3>")
            continue
        md_lines.append(f"\n### `{name}`\n")
        md_lines.append("| Column | Null Rate | Null Count |")
        md_lines.append("|---|---:|---:|")
        hrows = [f"<tr><th>Column</th><th>Null Rate</th><th>Null Count</th></tr>"]
        for col, rate in significant.sort_values(ascending=False).items():
            count = int(df[col].isna().sum())
            badge = " 🔴" if rate > 0.2 else (" 🟡" if rate > 0.05 else "")
            md_lines.append(f"| `{col}` | {rate*100:.2f}%{badge} | {count:,} |")
            cls = 'class="bad"' if rate > 0.2 else ('class="warn"' if rate > 0.05 else "")
            hrows.append(f"<tr {cls}><td><code>{html_escape(col)}</code></td><td>{rate*100:.2f}%</td><td>{count:,}</td></tr>")
        html_parts.append(f"<h3><code>{html_escape(name)}</code></h3><table>{''.join(hrows)}</table>")
    return "\n".join(md_lines) + "\n", "\n".join(html_parts) + "\n"


def _duplicate_rates_section(clean_report: Any) -> tuple[str, str]:
    md_lines = ["## 4. Duplicate Removal Summary\n"]
    md_lines.append("(Reported by Stage 2 — Data Cleaning)\n")
    md_lines.append("| Table | Duplicates Removed |")
    md_lines.append("|---|---:|")
    html_rows = ["<tr><th>Table</th><th>Duplicates Removed</th></tr>"]
    dups = getattr(clean_report, "duplicates_removed", {}) if clean_report else {}
    for table, count in dups.items():
        md_lines.append(f"| `{table}` | {count:,} |")
        html_rows.append(f"<tr><td><code>{html_escape(table)}</code></td><td>{count:,}</td></tr>")
    if not dups:
        md_lines.append("| _(none)_ | 0 |")
        html_rows.append("<tr><td><em>(none)</em></td><td>0</td></tr>")
    md = "\n".join(md_lines) + "\n"
    html = f"<h2>4. Duplicate Removal Summary</h2><table>{''.join(html_rows)}</table>\n"
    return md, html


def _timestamp_ranges_section(frames: dict[str, pd.DataFrame]) -> tuple[str, str]:
    md_lines = ["## 5. Timestamp Range Sanity\n"]
    md_lines.append("| Table | Timestamp Column | Earliest | Latest | Range (days) |")
    md_lines.append("|---|---|---|---:|---:|")
    html_rows = ["<tr><th>Table</th><th>Column</th><th>Earliest</th><th>Latest</th><th>Range (days)</th></tr>"]
    candidates = {
        "task_events": "event_time",
        "tasks": "created_at",
        "interruptions": "start_time",
        "users": "created_at",
        "locations": "created_at",
    }
    for table, col in candidates.items():
        if table not in frames or col not in frames[table].columns:
            continue
        df = frames[table]
        series = pd.to_datetime(df[col], errors="coerce", utc=True).dropna()
        if series.empty:
            continue
        earliest = series.min()
        latest = series.max()
        days = (latest - earliest).total_seconds() / 86400.0
        md_lines.append(f"| `{table}` | `{col}` | {earliest:%Y-%m-%d %H:%M} | {latest:%Y-%m-%d %H:%M} | {days:.1f} |")
        html_rows.append(
            f"<tr><td><code>{html_escape(table)}</code></td><td><code>{html_escape(col)}</code></td>"
            f"<td>{earliest:%Y-%m-%d %H:%M}</td><td>{latest:%Y-%m-%d %H:%M}</td><td>{days:.1f}</td></tr>"
        )
    md = "\n".join(md_lines) + "\n"
    html = f"<h2>5. Timestamp Range Sanity</h2><table>{''.join(html_rows)}</table>\n"
    return md, html


def _event_sequence_section(frames: dict[str, pd.DataFrame], validation_report: Any) -> tuple[str, str]:
    md_lines = ["## 3. Event Sequence Validity\n"]
    issues_count = 0
    seq_issues = 0
    if validation_report is not None:
        all_issues = getattr(validation_report, "issues", [])
        issues_count = len(all_issues)
        seq_issues = sum(1 for i in all_issues if getattr(i, "rule", "") == "impossible_sequence")
    md_lines.append(f"- Total validation issues: **{issues_count}**")
    md_lines.append(f"- Impossible sequence events (terminal→open): **{seq_issues}**\n")

    events_df = frames.get("task_events", pd.DataFrame())
    if not events_df.empty and "task_id" in events_df.columns and "event_type" in events_df.columns:
        terminal = {"completed", "forgotten", "cancelled"}
        open_types = {"created", "started", "resumed"}
        per_task_counts = []
        for task_id, grp in events_df.groupby("task_id"):
            types = [str(t).lower() for t in grp["event_type"]]
            n_open = sum(1 for t in types if t in open_types)
            n_term = sum(1 for t in types if t in terminal)
            per_task_counts.append((n_open, n_term))
        if per_task_counts:
            avg_open = np.mean([p[0] for p in per_task_counts])
            avg_term = np.mean([p[1] for p in per_task_counts])
            tasks_without_close = sum(1 for o, t in per_task_counts if o > 0 and t == 0)
            md_lines.append(f"- Total tasks with events: **{len(per_task_counts):,}**")
            md_lines.append(f"- Avg open events per task: **{avg_open:.2f}**")
            md_lines.append(f"- Avg terminal events per task: **{avg_term:.2f}**")
            md_lines.append(f"- Tasks with ≥1 open but no terminal event: **{tasks_without_close:,}** (dangling sessions)\n")

    md = "\n".join(md_lines) + "\n"
    html = f"<h2>3. Event Sequence Validity</h2>\n<pre>{html_escape(md)}</pre>\n"
    return md, html


def _class_balance_section(feature_df: pd.DataFrame) -> tuple[str, str]:
    md_lines = ["## 6. ML Target — Class Balance\n"]
    if feature_df.empty or "will_forget" not in feature_df.columns:
        md_lines.append("_No feature matrix available_\n")
        return "\n".join(md_lines), "<h2>6. ML Target — Class Balance</h2><p><em>No feature matrix available</em></p>"
    total = len(feature_df)
    pos = int(feature_df["will_forget"].sum())
    neg = total - pos
    pos_rate = pos / total * 100
    md_lines.append(f"Target column: `will_forget` (1 = task was forgotten)\n")
    md_lines.append("| Class | Count | Percentage |")
    md_lines.append("|---|---:|---:|")
    md_lines.append(f"| 0 (not forgotten) | {neg:,} | {100-pos_rate:.1f}% |")
    md_lines.append(f"| 1 (forgotten)     | {pos:,} | {pos_rate:.1f}% |")
    md_lines.append(f"| **Total**         | **{total:,}** | **100%** |")
    balance_note = "⚠ Imbalanced — consider class weights or SMOTE" if pos_rate < 10 or pos_rate > 40 else "✓ Reasonably balanced"
    md_lines.append(f"\n{balance_note} (positive rate = {pos_rate:.1f}%)\n")
    html_rows = ["<tr><th>Class</th><th>Count</th><th>Percentage</th></tr>"]
    html_rows.append(f"<tr><td>0 (not forgotten)</td><td>{neg:,}</td><td>{100-pos_rate:.1f}%</td></tr>")
    html_rows.append(f"<tr><td>1 (forgotten)</td><td>{pos:,}</td><td>{pos_rate:.1f}%</td></tr>")
    html_rows.append(f"<tr><td><strong>Total</strong></td><td><strong>{total:,}</strong></td><td>100%</td></tr>")
    html = (
        f"<h2>6. ML Target — Class Balance</h2>"
        f"<p>Target column: <code>will_forget</code></p>"
        f"<table>{''.join(html_rows)}</table>"
        f"<p>{html_escape(balance_note)}</p>\n"
    )
    return "\n".join(md_lines) + "\n", html


def _feature_completeness_section(feature_df: pd.DataFrame) -> tuple[str, str]:
    md_lines = ["## 7. Feature Completeness\n"]
    if feature_df.empty:
        md_lines.append("_No feature matrix available_\n")
        return "\n".join(md_lines), "<h2>7. Feature Completeness</h2><p><em>No feature matrix available</em></p>"
    feature_cols = [c for c in feature_df.columns if c not in {"task_id", "user_id", "created_at", "status", "will_forget", "task_location_pair"}]
    if not feature_cols:
        md_lines.append("_No feature columns found_\n")
        return "\n".join(md_lines), "<h2>7. Feature Completeness</h2><p><em>No feature columns found</em></p>"
    completeness = feature_df[feature_cols].notna().mean()
    overall = float(completeness.mean()) * 100
    md_lines.append(f"- Feature count: **{len(feature_cols)}**")
    md_lines.append(f"- Overall mean completeness: **{overall:.1f}%**\n")
    md_lines.append("### Low-completeness Features (<90% populated)\n")
    md_lines.append("| Feature | Completeness | Null Rate |")
    md_lines.append("|---|---:|---:|")
    html_rows = ["<tr><th>Feature</th><th>Completeness</th><th>Null Rate</th></tr>"]
    low = completeness[completeness < 0.9].sort_values()
    if low.empty:
        md_lines.append("| _(none — all features ≥90% complete)_ | | |")
        html_rows.append('<tr><td colspan="3"><em>All features ≥90% complete</em></td></tr>')
    else:
        for feat, comp in low.items():
            nr = (1 - comp) * 100
            md_lines.append(f"| `{feat}` | {comp*100:.1f}% | {nr:.1f}% |")
            cls = 'class="bad"' if comp < 0.5 else 'class="warn"'
            html_rows.append(f"<tr {cls}><td><code>{html_escape(feat)}</code></td><td>{comp*100:.1f}%</td><td>{nr:.1f}%</td></tr>")
    md = "\n".join(md_lines) + "\n"
    html = f"<h2>7. Feature Completeness</h2><p>Features: {len(feature_cols)}, mean completeness: {overall:.1f}%</p><table>{''.join(html_rows)}</table>\n"
    return md, html


def _validation_section(validation_report: Any, clean_report: Any) -> tuple[str, str]:
    md_lines = ["## 8. Validation & Cleaning Summary\n"]
    if validation_report is not None:
        md_lines.append(f"- Validation issues: **{len(getattr(validation_report, 'issues', []))}**")
        md_lines.append(f"  - Errors: **{len(getattr(validation_report, 'errors', []))}**")
        md_lines.append(f"  - Warnings: **{len(getattr(validation_report, 'warnings', []))}**")
    if clean_report is not None:
        md_lines.append(f"- Cleaning operations performed:")
        md_lines.append(f"  - Timezone normalized: **{getattr(clean_report, 'tz_normalized', {})}**")
        md_lines.append(f"  - Durations imputed: **{getattr(clean_report, 'durations_imputed', 0)}**")
        md_lines.append(f"  - End times imputed: **{getattr(clean_report, 'end_times_imputed', 0)}**")
        md_lines.append(f"  - Categories normalized: **{getattr(clean_report, 'categories_normalized', 0)}**")
        md_lines.append(f"  - Anomalies flagged: **{getattr(clean_report, 'anomalies_flagged', 0)}**")
        md_lines.append(f"  - Priorities clamped: **{getattr(clean_report, 'priorities_clamped', 0)}**\n")
    md = "\n".join(md_lines) + "\n"
    html = f"<h2>8. Validation & Cleaning Summary</h2>\n<pre>{html_escape(md)}</pre>\n"
    return md, html


# ── public entrypoint ────────────────────────────────────────────────────────

def generate_quality_report(
    *,
    frames: dict[str, pd.DataFrame],
    validation_report: Any = None,
    clean_report: Any = None,
    feature_df: pd.DataFrame | None = None,
    sessions_df: pd.DataFrame | None = None,
    output_dir: str | Path = "data",
) -> dict[str, str]:
    """
    Generate Markdown + HTML data quality reports.

    Returns dict with keys: "markdown", "html" → absolute output file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    feature_df = feature_df if feature_df is not None else pd.DataFrame()
    sessions_df = sessions_df if sessions_df is not None else pd.DataFrame()
    all_frames = dict(frames)
    if not sessions_df.empty:
        all_frames.setdefault("sessions", sessions_df)
    if not feature_df.empty:
        all_frames.setdefault("features", feature_df)

    title = "# ContextIQ — Data Quality Report\n"
    subtitle = f"_Generated: {datetime.now(timezone.utc).isoformat()} (UTC). All data is synthetic._\n\n"
    toc = (
        "**Table of Contents**\n"
        "1. [Record Counts per Table](#1-record-counts-per-table)\n"
        "2. [Null Rates per Column](#2-null-rates-per-column)\n"
        "3. [Event Sequence Validity](#3-event-sequence-validity)\n"
        "4. [Duplicate Removal Summary](#4-duplicate-removal-summary)\n"
        "5. [Timestamp Range Sanity](#5-timestamp-range-sanity)\n"
        "6. [ML Target — Class Balance](#6-ml-target--class-balance)\n"
        "7. [Feature Completeness](#7-feature-completeness)\n"
        "8. [Validation & Cleaning Summary](#8-validation--cleaning-summary)\n\n"
    )

    md_parts = [title, subtitle, toc]
    md_1, html_1 = _table_counts_section(all_frames)
    md_2, html_2 = _null_rates_section(all_frames)
    md_3, html_3 = _event_sequence_section(all_frames, validation_report)
    md_4, html_4 = _duplicate_rates_section(clean_report)
    md_5, html_5 = _timestamp_ranges_section(all_frames)
    md_6, html_6 = _class_balance_section(feature_df)
    md_7, html_7 = _feature_completeness_section(feature_df)
    md_8, html_8 = _validation_section(validation_report, clean_report)

    md_parts.extend([md_1, md_2, md_3, md_4, md_5, md_6, md_7, md_8])
    md_text = "\n".join(md_parts)
    md_path = out / "quality_report.md"
    md_path.write_text(md_text, encoding="utf-8")
    logger.info("Markdown report: %s", md_path)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ContextIQ Data Quality Report</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; color: #1f2937; }}
h1 {{ color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: .5rem; }}
h2 {{ color: #1e40af; margin-top: 2.5rem; }}
h3 {{ color: #1d4ed8; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.92rem; }}
th, td {{ border: 1px solid #e5e7eb; padding: .5rem .75rem; text-align: left; }}
th {{ background: #eff6ff; }}
tr.bad {{ background: #fef2f2; }}
tr.warn {{ background: #fffbeb; }}
code {{ background: #f3f4f6; padding: .1rem .3rem; border-radius: 4px; font-size: .85em; }}
pre {{ background: #f8fafc; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
.meta {{ color: #6b7280; font-size: .9rem; }}
</style>
</head>
<body>
<h1>ContextIQ — Data Quality Report</h1>
<p class="meta">Generated: {datetime.now(timezone.utc).isoformat()} (UTC). All data is synthetic.</p>
{html_1}{html_2}{html_3}{html_4}{html_5}{html_6}{html_7}{html_8}
</body>
</html>
"""
    html_path = out / "quality_report.html"
    html_path.write_text(html_doc, encoding="utf-8")
    logger.info("HTML report: %s", html_path)

    return {
        "markdown": str(md_path),
        "html": str(html_path),
    }
