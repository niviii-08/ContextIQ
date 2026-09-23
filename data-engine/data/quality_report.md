# ContextIQ — Data Quality Report

_Generated: 2026-08-19T16:17:04.293903+00:00 (UTC). All data is synthetic._


**Table of Contents**
1. [Record Counts per Table](#1-record-counts-per-table)
2. [Null Rates per Column](#2-null-rates-per-column)
3. [Event Sequence Validity](#3-event-sequence-validity)
4. [Duplicate Removal Summary](#4-duplicate-removal-summary)
5. [Timestamp Range Sanity](#5-timestamp-range-sanity)
6. [ML Target — Class Balance](#6-ml-target--class-balance)
7. [Feature Completeness](#7-feature-completeness)
8. [Validation & Cleaning Summary](#8-validation--cleaning-summary)


## 1. Record Counts per Table

| Table | Rows | Columns |
|---|---:|---:|
| `features` | 13,799 | 29 |
| `interruptions` | 19,327 | 12 |
| `locations` | 120 | 8 |
| `sessions` | 24,790 | 10 |
| `task_events` | 63,888 | 13 |
| `tasks` | 13,799 | 20 |
| `users` | 50 | 6 |

## 2. Null Rates per Column


### `features`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `deadline_distance_hours` | 59.57% 🔴 | 8,220 |
| `hour_forgetting_rate` | 8.30% 🟡 | 1,145 |
| `category_forgetting_rate` | 2.90% | 400 |
| `days_since_last_similar` | 2.90% | 400 |
| `weekday_forgetting_rate` | 2.57% | 354 |
| `recovery_time_s` | 0.99% | 137 |
| `location_forgetting_rate` | 0.88% | 121 |
| `avg_interruption_duration_s` | 0.86% | 118 |
| `context_switch_rate_7d` | 0.39% | 54 |
| `avg_session_duration_7d_s` | 0.39% | 54 |
| `completion_rate` | 0.37% | 51 |
| `daily_friction_score` | 0.37% | 51 |

### `interruptions`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `source_label` | 100.00% 🔴 | 19,327 |

### `locations`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `latitude` | 100.00% 🔴 | 120 |
| `longitude` | 100.00% 🔴 | 120 |

### `sessions`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `resume_delay_seconds` | 60.23% 🔴 | 14,930 |

### `task_events`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `event_metadata` | 100.00% 🔴 | 63,888 |
| `inter_event_gap_s` | 21.60% 🔴 | 13,799 |

### `tasks`

| Column | Null Rate | Null Count |
|---|---:|---:|
| `cancelled_at` | 95.51% 🔴 | 13,180 |
| `forgotten_at` | 75.97% 🔴 | 10,483 |
| `deadline_distance_h` | 59.57% 🔴 | 8,220 |
| `deadline_at` | 59.57% 🔴 | 8,220 |
| `task_duration_h` | 28.52% 🔴 | 3,935 |
| `completed_at` | 28.52% 🔴 | 3,935 |
| `started_at` | 12.41% 🟡 | 1,713 |
| `task_age_at_start_h` | 12.41% 🟡 | 1,713 |

### `users` — all columns fully populated (≤0.1% nulls)


## 3. Event Sequence Validity

- Total validation issues: **64**
- Impossible sequence events (terminal→open): **0**

- Total tasks with events: **13,799**
- Avg open events per task: **2.67**
- Avg terminal events per task: **1.00**
- Tasks with ≥1 open but no terminal event: **0** (dangling sessions)


## 4. Duplicate Removal Summary

(Reported by Stage 2 — Data Cleaning)

| Table | Duplicates Removed |
|---|---:|
| `events` | 0 |
| `interruptions` | 0 |
| `tasks` | 0 |

## 5. Timestamp Range Sanity

| Table | Timestamp Column | Earliest | Latest | Range (days) |
|---|---|---|---:|---:|
| `task_events` | `event_time` | 2026-06-20 00:36 | 2026-08-22 10:54 | 63.4 |
| `tasks` | `created_at` | 2026-06-20 00:36 | 2026-08-18 23:36 | 60.0 |
| `interruptions` | `start_time` | 2026-06-20 01:11 | 2026-08-20 05:23 | 61.2 |
| `users` | `created_at` | 2026-06-20 15:49 | 2026-06-20 15:49 | 0.0 |
| `locations` | `created_at` | 2026-06-20 15:49 | 2026-06-20 15:49 | 0.0 |

## 6. ML Target — Class Balance

Target column: `will_forget` (1 = task was forgotten)

| Class | Count | Percentage |
|---|---:|---:|
| 0 (not forgotten) | 10,483 | 76.0% |
| 1 (forgotten)     | 3,316 | 24.0% |
| **Total**         | **13,799** | **100%** |

✓ Reasonably balanced (positive rate = 24.0%)


## 7. Feature Completeness

- Feature count: **23**
- Overall mean completeness: **96.5%**

### Low-completeness Features (<90% populated)

| Feature | Completeness | Null Rate |
|---|---:|---:|
| `deadline_distance_hours` | 40.4% | 59.6% |

## 8. Validation & Cleaning Summary

- Validation issues: **64**
  - Errors: **0**
  - Warnings: **64**
- Cleaning operations performed:
  - Timezone normalized: **{'events': 0, 'interruptions': 0, 'tasks': 0}**
  - Durations imputed: **0**
  - End times imputed: **0**
  - Categories normalized: **0**
  - Anomalies flagged: **0**
  - Priorities clamped: **0**

