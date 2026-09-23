# ContextIQ Limitations and Future Improvements

## Current Limitations

- The primary dataset is synthetic. It is useful for reproducibility and pipeline testing, not for validating human behaviour claims.
- The forgetting label reflects an application state, not a clinical or psychological construct.
- The core backend's development `X-User-Id` path is a placeholder until verified JWT/OIDC authentication is enabled in production.
- Model results may drift when task categories, event behaviour, devices, or user populations change.
- Association rules can reflect repetition without explaining why a task was repeated.
- SHAP describes model behaviour and is not causal evidence.
- Optional LLM output can still be incomplete or stylistically wrong; structured validation and mock mode reduce, but do not eliminate, this risk.
- Service-level rate limiting, distributed tracing, metrics export, and centralized log aggregation are deployment responsibilities not fully implemented in this repository.
- Some full integration tests require heavyweight ML training and an installed service-specific environment.

## Future Improvements

1. Implement verified JWT/OIDC authentication and authorization across every service.
2. Add durable idempotency keys and event lineage for ingestion retries.
3. Add PostgreSQL-backed integration tests to CI and a clean Docker smoke test.
4. Add model registry/version promotion, drift monitoring, calibration monitoring, and rollback.
5. Evaluate subgroup performance, missingness, and fairness on consented representative data.
6. Add explicit data retention, deletion, export, and consent controls.
7. Introduce OpenTelemetry traces and service-level metrics.
8. Add a deployment-edge rate limiter and request-size limits.
9. Improve association evaluation with offline recommendation metrics and user feedback.
10. Keep LLM outputs grounded in validated evidence with citation-like source fields and abstention on insufficient data.
