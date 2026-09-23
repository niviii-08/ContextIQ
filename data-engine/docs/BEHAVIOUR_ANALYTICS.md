# Behaviour Analytics

This document explains, in full, how every metric in the system is
calculated: the Context Session Engine's reconstruction algorithm, every
behavioural metric, and the experimental Friction Score formula.

---

## 1. Context Session Engine

**Source:** `app/services/session_engine.py`

### What a "context session" is

A context session is a contiguous block of time a user spends engaged
with one task, bounded by an opening event and a closing event:

- **Opens on:** `created`, `started`, `resumed`
- **Closes on:** `paused`, `completed`, `forgotten`, `cancelled`

A single task can span **multiple** sessions if it is paused and resumed
(each pause→resume boundary ends one session and starts another).

### Algorithm, step by step

For each task, independently:

1. Sort `task_events` chronologically.
2. Walk events pairwise: an "open" event followed eventually by a "close"
   event defines one raw session window `[start, end]`.
3. Gather all `interruptions` for that task that **overlap** the session
   window (an interruption overlaps if its `[start_time, end_time]` range
   intersects `[session_start, session_end]`).
4. **`focused_time_seconds`** = session duration − total overlapping
   interruption time (clamped to ≥ 0).
5. **`interruption_time_seconds`** = sum of overlapping interruption
   durations (only the portion that falls inside the session window is
   counted, in case an interruption started before the session or ends
   after it).
6. **`resume_delay_seconds`** — only computed for sessions that open on a
   `resumed` event: the gap between the immediately preceding `paused`
   event on this task and this `resumed` event. This measures how long
   it took the person to come back after pausing.
7. **`context_switch_count`** — **not every interruption counts as a
   context switch.** An interruption is counted as a context switch only
   if its duration is **≥ `CONTEXT_SWITCH_GAP_MINUTES`** (default: 5
   minutes, configurable via `.env`). Shorter interruptions are still
   recorded in `interruption_count` / `interruption_time_seconds`, but are
   not counted as a switch, because the underlying assumption is: a
   30-second glance at a phone rarely costs real re-orientation time,
   while an 8-minute detour usually does.
8. **Dangling sessions:** if a task's last event is an "open" event with
   no closing event yet (e.g. still `started` as of now), the session is
   closed at `min(open_event_time + SESSION_IDLE_TIMEOUT_MINUTES, now)`
   (default idle timeout: 30 minutes) purely for analytics purposes — this
   does **not** alter the underlying task's real status.

### Idempotency

`rebuild_sessions_for_user(db, user_id)` **deletes and regenerates every**
`context_sessions` row for that user from scratch on every call. It is
always safe to call repeatedly after new events arrive; there is no
incremental/partial state to get out of sync.

---

## 2. Task-level metrics

**Source:** `app/analytics/metrics.py`

All rate metrics are computed over **resolved** tasks only — i.e. tasks
whose status is `completed`, `forgotten`, or `cancelled`. Tasks still in
`created`/`started`/`paused`/`resumed` are excluded from rate
denominators (they haven't reached an outcome yet).

- **`task_completion_rate`** = completed / resolved
- **`task_forgetting_rate`** = forgotten / resolved
- **`average_task_duration_minutes`** = mean(`completed_at` − `started_at`)
  over completed tasks with both timestamps present
- **`average_task_delay_minutes`** = mean(`completed_at` − `deadline_at`)
  over tasks that had a deadline and were completed (positive = late)
- **`tasks_per_day`** = total tasks in period / period_days
- **`tasks_per_category`** / **`tasks_per_location`** — simple counts,
  grouped
- **`forgetting_by_weekday`** / **`forgetting_by_hour`** — forgetting rate
  grouped by the weekday name / hour-of-day of `created_at`
- **`forgetting_by_category`** / **`forgetting_by_location`** — forgetting
  rate grouped by category / location

## 3. Interruption-level metrics

- **`interruption_count`**, **`interruption_duration_minutes_total`**,
  **`interruption_duration_minutes_avg`** — straightforward aggregates
- **`interruption_by_weekday`** / **`interruption_by_hour`** /
  **`interruption_by_category`** — simple counts grouped by the
  interruption's `start_time` weekday/hour, or by `interruption_type`

## 4. Context-session-level metrics

- **`average_focus_session_minutes`** = mean(`focused_time_seconds`) / 60
  across all reconstructed sessions
- **`total_context_switches`** = sum(`context_switch_count`)
- **`resume_count`** = number of sessions with a non-null
  `resume_delay_seconds` (i.e. sessions that were actual resumptions)
- **`pause_count`** = count of raw `paused` events in `task_events`
- **`average_resume_delay_seconds`** = mean(`resume_delay_seconds`) over
  sessions where it's set
- **`context_switching_by_task_category`** / **`context_switching_by_location`**
  — `context_switch_count` summed, grouped by the parent task's category /
  the session's location

---

## 5. Experimental Behavioural Friction Score

**Source:** `app/analytics/friction.py`

> **Experimental behavioural metric — not scientifically validated.**
> This is a deliberately simple, transparent heuristic — not a clinically
> validated instrument. It exists to give a single explainable number, not
> a ground-truth measurement of "how bad someone's day was."

### Components (each 0–100, higher = worse friction)

1. **`forgetting_score`** = `100 × task_forgetting_rate`

2. **`interruption_score`** = `100 × min(1, interruptions_per_active_hour / 6)`
   where `interruptions_per_active_hour = total interruptions / (total
   focused+interruption seconds across sessions, in hours)`. The
   saturation point (6/hr) is a normalization ceiling, not an empirically
   derived threshold.

3. **`context_switch_score`** = `100 × min(1, (context_switches / sessions) / 3)`
   — saturates at 3 switches per session.

4. **`recovery_score`** = `100 × min(1, average_resume_delay_minutes / 30)`
   — saturates at a 30-minute average resume delay.

### Overall score

```
overall_score = 0.35 × forgetting_score
              + 0.25 × interruption_score
              + 0.20 × context_switch_score
              + 0.20 × recovery_score
```

The weights encode an explicit, documented (not empirically derived)
assumption: losing an entire task (forgetting) is the costliest form of
friction, interruptions are the next most costly, and switch-frequency /
slow recovery matter but somewhat less. **These weights are named
constants in `app/analytics/friction.py` and are the first thing to
recalibrate once real usage data exists.**

All sub-scores and the overall score are clamped to `[0, 100]`.
