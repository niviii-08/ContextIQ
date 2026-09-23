"""
ContextIQ Data Engineering Pipeline
=====================================

End-to-end behavioural data pipeline:

  Raw Events
    -> Stage 1: Validation       (validate.py)
    -> Stage 2: Cleaning         (clean.py)
    -> Stage 3: Transformation   (transform.py)
    -> Stage 4: Session Recon    (reconstruct.py)
    -> Stage 5: Feature Eng.     (features.py)
    -> Stage 6: ML Export        (ml_export.py)
    -> Stage 7: Model Training   (model.py)
    -> Stage 8: Analytics Pop.   (populate_analytics.py)
    -> Stage 9: Quality Report   (quality_report.py)

Orchestrated by: run_pipeline.py
"""
