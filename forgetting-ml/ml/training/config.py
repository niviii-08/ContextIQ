"""
config.py

Centralized hyperparameter and training configuration.
Keeping tunables here (rather than inline) makes the pipeline reproducible
and easy to audit - a recruiter reading this file can immediately see what
knobs were turned and why.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any


SEED: int = 42

MODEL_VERSION: str = "1.1.0"

DATASET_VERSION: str = "1.0.0"

SPLIT_CONFIG: Dict[str, float] = {
    "train_frac": 0.70,
    "val_frac": 0.15,
}

DATASET_CONFIG: Dict[str, Any] = {
    "n_users": 100,
    "n_days": 95,
    "min_observations": 10000,
    "seed": SEED,
}


@dataclass
class LogisticRegressionParams:
    max_iter: int = 1000
    class_weight: str = "balanced"
    C: float = 1.0
    solver: str = "lbfgs"
    random_state: int = SEED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RandomForestParams:
    n_estimators: int = 400
    max_depth: int = 12
    min_samples_leaf: int = 15
    min_samples_split: int = 40
    class_weight: str = "balanced_subsample"
    max_features: str = "sqrt"
    bootstrap: bool = True
    oob_score: bool = False
    random_state: int = SEED
    n_jobs: int = -1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class XGBoostParams:
    n_estimators: int = 500
    max_depth: int = 5
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    colsample_bylevel: float = 0.9
    min_child_weight: int = 5
    reg_alpha: float = 0.1
    reg_lambda: float = 1.0
    gamma: float = 0.0
    eval_metric: str = "logloss"
    objective: str = "binary:logistic"
    tree_method: str = "hist"
    random_state: int = SEED
    n_jobs: int = -1

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


THRESHOLD_TUNING = {
    "metric": "f1",
    "min_threshold": 0.05,
    "max_threshold": 0.95,
    "n_thresholds": 181,
}

CALIBRATION_CONFIG = {
    "methods": ["isotonic", "sigmoid"],
    "cv": "prefit",
}

CROSS_VALIDATION_CONFIG = {
    "n_splits": 5,
    "strategy": "time_series",
    "gap": 0,
}

SHAP_CONFIG = {
    "n_background_samples": 200,
    "n_summary_samples": 500,
    "top_k_features": 20,
}
