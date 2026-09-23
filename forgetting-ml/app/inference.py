"""
inference.py

Loads the trained model bundle exactly once and exposes single / batch
prediction functions. No hardcoded predictions - every call routes through
the trained model artifact.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_LOCAL_DEPS = ROOT / "pydeps"
if _LOCAL_DEPS.exists():
    sys.path.insert(0, str(_LOCAL_DEPS))

from ml.explainability.explainer import ForgettingExplainer, risk_level_from_probability
from ml.training.config import MODEL_VERSION

ARTIFACT_PATH = ROOT / "artifacts" / "model_bundle.joblib"


class ForgettingPredictor:
    _instance = None

    def __init__(self):
        if not ARTIFACT_PATH.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {ARTIFACT_PATH}. "
                "Run `python -m ml.training.train` first."
            )
        bundle = joblib.load(ARTIFACT_PATH)
        if not isinstance(bundle, dict):
            raise ValueError("Model artifact has an invalid format.")
        required_keys = {
            "model", "raw_model", "preprocessor", "model_name", "model_version",
            "threshold", "calibrated", "categorical_features", "numeric_features",
            "feature_names_transformed",
        }
        missing_keys = sorted(required_keys - bundle.keys())
        if missing_keys:
            raise ValueError(f"Model artifact is missing required fields: {missing_keys}")
        if bundle["model_version"] != MODEL_VERSION:
            raise ValueError(
                f"Model artifact version {bundle['model_version']!r} does not match "
                f"runtime version {MODEL_VERSION!r}."
            )
        if not isinstance(bundle["categorical_features"], list) or not isinstance(bundle["numeric_features"], list):
            raise ValueError("Model artifact feature metadata is invalid.")
        self.model = bundle["model"]
        self.raw_model = bundle["raw_model"]
        self.preprocessor = bundle["preprocessor"]
        self.model_name = bundle["model_name"]
        self.model_version = bundle["model_version"]
        self.threshold = bundle["threshold"]
        self.calibrated = bundle["calibrated"]
        self.categorical_features = bundle["categorical_features"]
        self.numeric_features = bundle["numeric_features"]
        self.feature_names_transformed = bundle["feature_names_transformed"]
        self.background_sample = bundle.get("background_sample")

        self.explainer = ForgettingExplainer(
            raw_model=self.raw_model,
            model_name=self.model_name,
            preprocessor=self.preprocessor,
            feature_names_transformed=self.feature_names_transformed,
            background_data=self.background_sample,
        )

    @classmethod
    def instance(cls) -> "ForgettingPredictor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _to_dataframe(self, tasks: List[Dict[str, Any]]) -> pd.DataFrame:
        cols = self.categorical_features + self.numeric_features
        missing_by_task = {
            index: [column for column in cols if column not in task]
            for index, task in enumerate(tasks)
        }
        missing_by_task = {index: missing for index, missing in missing_by_task.items() if missing}
        if missing_by_task:
            raise ValueError(f"Missing required features by task: {missing_by_task}")
        df = pd.DataFrame(tasks)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required features: {missing}")
        return df[cols]

    def predict_batch(self, tasks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        if not tasks:
            return []

        df = self._to_dataframe(tasks)
        X_transformed = self.preprocessor.transform(df)
        if hasattr(X_transformed, "toarray"):
            X_transformed = X_transformed.toarray()

        probabilities = np.asarray(self.model.predict_proba(X_transformed))
        if probabilities.ndim != 2 or probabilities.shape[0] != len(tasks) or probabilities.shape[1] < 2:
            raise ValueError("Model returned an invalid probability matrix.")
        probabilities = probabilities[:, 1]
        if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
            raise ValueError("Model returned invalid prediction probabilities.")

        results = []
        for i, task in enumerate(tasks):
            row = X_transformed[i:i + 1]
            prob = float(probabilities[i])
            reasons = self.explainer.explain(row, top_k=top_k)
            results.append({
                "task": task.get("task_id"),
                "prediction_probability": round(prob, 4),
                "risk_level": risk_level_from_probability(prob),
                "model_version": self.model_version,
                "top_features": reasons,
            })
        return results

    def predict_single(self, task: Dict[str, Any], top_k: int = 3) -> Dict[str, Any]:
        return self.predict_batch([task], top_k=top_k)[0]
