# ContextIQ Feature Dictionary

The canonical detailed dictionary is maintained in [data-engine/docs/FEATURE_DICTIONARY.md](../data-engine/docs/FEATURE_DICTIONARY.md). This page gives the recruiter-facing map of the feature groups and their meaning.

## Target

| Field | Definition |
|---|---|
| `will_forget` | `1` when the task's eventual status is `forgotten`, otherwise `0` |

## Categorical Inputs

| Feature | Meaning |
|---|---|
| `task_category` | Task domain such as Academic, Work, Personal, Health, Household, Social, or Finance |
| `priority` | Declared task urgency/importance |
| `location` | Context or location associated with the task |

## Historical Behaviour Features

| Feature group | Examples | Why it matters |
|---|---|---|
| Prior outcomes | Previous completion count, previous forgetting count, historical completion/forgetting rates | Captures each user's observed history without using the current outcome |
| Repetition | Task frequency, days since last similar task, repeated context count | Captures recurring task/context patterns |
| Temporal load | Tasks today, weekday/hour, late-night indicator, deadline distance | Captures timing and workload pressure |
| Disruptions | Interruptions today, average interruption duration, recent context switches | Captures attention fragmentation |
| Recovery | Recovery time, average session duration, context-switch rate | Captures the cost of returning to work |
| Composite friction | Rolling daily friction and 7-day context metrics | Summarizes recent behavioural strain |

## Metadata Excluded From Training

`task_id`, `user_id`, raw `created_at`, raw status, and other identifiers are retained for joins, auditing, or evaluation but are not training predictors.

## Leakage Rule

For every task row, feature construction uses only records with timestamps strictly before `created_at`. The target is computed separately from the eventual outcome. See the full field-by-field formulas and examples in the [canonical dictionary](../data-engine/docs/FEATURE_DICTIONARY.md).
