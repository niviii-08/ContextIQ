# Privacy Boundaries

This module operates exclusively on already-computed, structured behavioural
outputs (predictions, associations, metrics). It does not, and must not,
perform any of the following:

- Reading private messages (email, chat, SMS content, etc.)
- Screen monitoring or screen recording
- Keylogging or input capture
- General surveillance of user activity outside the defined input schemas

## What data this module sees

Only the fields defined in `app/schemas.py`:
`ForgettingPrediction`, `ContextInsight`, `Association`, `BehaviourMetric`,
and user feedback (`FeedbackEntry`). These are numeric/categorical summaries
already produced by upstream ML systems — never raw personal content.

## What the LLM sees

The LLM explanation layer receives only the small, already-validated JSON
payload for a single insight or recommendation being explained (see
`docs/LLM_ARCHITECTURE.md`). It never receives raw user data, message
content, or anything outside the structured schemas above.

## Feedback storage

`FeedbackEntry` records store a `user_id`, a target reference, a feedback
category, and an optional free-text `comment` the user chooses to write. The
default `InMemoryFeedbackStore` keeps this in process memory only (not
persisted to disk). A production deployment should back `FeedbackStore` with
an access-controlled database and apply the same data-minimization principle
already used here — do not add fields beyond what's needed to act on
feedback.

## Extending this module

Any future contributor adding new input types to `schemas.py` should ask: is
this a structured, already-computed behavioural summary, or is it raw
personal content (messages, keystrokes, screen contents)? Only the former
belongs in this module's input contract.
