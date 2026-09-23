# ContextIQ Responsible Use and Privacy

## Responsible Use

ContextIQ is a personal productivity and behavioural analytics demonstration. It must not be used to diagnose health conditions, rank employees or students, make hiring decisions, determine creditworthiness, or infer sensitive traits.

A forgetting-risk score is a model estimate based on observed task history. It should support a user's own reflection and planning, not automate consequential decisions about them.

## Data Boundaries

The system is designed around explicit events: task lifecycle events, interruptions, timestamps, contexts, and session signals. It should not collect keystrokes, message contents, microphone data, screen recordings, or unrelated browsing history. The intelligence layer should receive the minimum structured evidence required for an explanation.

## User Controls

A production deployment should provide clear consent, visibility into collected events, correction of bad data, export, deletion, retention controls, and opt-out. Synthetic demo data does not require real-person consent, but production data does.

## Security Expectations

- Keep database credentials, signing keys, and LLM keys in a secret manager or server environment.
- Never place secrets in `NEXT_PUBLIC_*` variables or browser storage.
- Restrict CORS to known origins.
- Use verified authentication and user-scoped authorization.
- Log request IDs and operational failures without logging tokens, prompts containing sensitive data, or raw behavioural histories.
- Protect model artifacts and backups because they can encode information about the training population.

## Model Transparency

Expose the model version, probability interpretation, top contributing features, data period, and limitations alongside predictions. SHAP explanations are associations, not causes. When evidence is insufficient, the correct behaviour is to abstain or show an unavailable state rather than invent certainty.
