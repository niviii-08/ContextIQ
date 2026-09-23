"""
Analytics Package
=================

Comprehensive behavioral analytics including:
- Derived metrics (forget risk, friction scores, etc.)
- Behavioral insights (answers to key questions)
- Statistical analysis (distributions, correlations, trends)
- Integration with existing metrics and friction modules
"""

from app.analytics import metrics as m
from app.analytics import friction as f
from app.analytics import derived_metrics as dm
from app.analytics import insights as ins
from app.analytics import statistical_analysis as sa

__all__ = [
    "metrics",
    "friction", 
    "derived_metrics",
    "insights",
    "statistical_analysis",
]
