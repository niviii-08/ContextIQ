"""
explainer.py

Produces human-readable "reasons" for a single prediction using SHAP values
(preferred, tree/linear model aware) with a graceful fallback to global
feature importances if SHAP fails for any reason.

IMPORTANT — causality disclaimer
---------------------------------
SHAP values and feature importances describe ASSOCIATION between input
features and the model's output probability. They do NOT establish that a
feature CAUSES forgetting. All generated reason strings are phrased in
correlational / descriptive language, never causal language ("X is
associated with higher risk" rather than "X causes higher risk").
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import shap

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from ml.features.feature_spec import FEATURE_DESCRIPTIONS

RISK_THRESHOLDS = {
    "LOW": 0.33,
    "MEDIUM": 0.66,
}


def risk_level_from_probability(prob: float) -> str:
    if prob < RISK_THRESHOLDS["LOW"]:
        return "LOW"
    elif prob < RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "HIGH"


def _map_transformed_name_to_raw(transformed_name: str) -> str:
    """
    Maps a ColumnTransformer output name like 'num__historical_forgetting_rate'
    or 'cat__task_category_Household' back to a human description.
    """
    if transformed_name.startswith("num__"):
        raw = transformed_name[len("num__"):]
        return FEATURE_DESCRIPTIONS.get(raw, raw)
    if transformed_name.startswith("cat__"):
        raw = transformed_name[len("cat__"):]
        # raw looks like "task_category_Household"
        for base in ("task_category", "priority", "location"):
            if raw.startswith(base + "_"):
                value = raw[len(base) + 1:]
                desc = FEATURE_DESCRIPTIONS.get(base, base)
                return f"{desc} = {value}"
        return raw
    return transformed_name


class ForgettingExplainer:
    def __init__(self, raw_model, model_name: str, preprocessor, feature_names_transformed: List[str],
                 background_data=None):
        self.raw_model = raw_model
        self.model_name = model_name
        self.preprocessor = preprocessor
        self.feature_names_transformed = feature_names_transformed
        self._explainer = None
        self._background = background_data
        self._build_explainer()

    def _build_explainer(self):
        try:
            if self.model_name in ("random_forest", "xgboost"):
                self._explainer = shap.TreeExplainer(self.raw_model)
            elif self.model_name == "logistic_regression":
                # Linear explainer needs a background dataset; fall back to
                # a small synthetic zero-background if none provided.
                bg = self._background
                self._explainer = shap.LinearExplainer(self.raw_model, bg, feature_perturbation="interventional")
            else:
                self._explainer = None
        except Exception:
            self._explainer = None

    def explain(self, X_transformed_row: np.ndarray, top_k: int = 3) -> List[str]:
        """
        Returns a list of top_k natural-language reason strings for a single
        transformed feature row (1 x n_features).
        """
        if self._explainer is None:
            return self._fallback_reasons(top_k)

        try:
            shap_values = self._explainer.shap_values(X_transformed_row)
            if isinstance(shap_values, list):
                # binary classification tree explainer sometimes returns [class0, class1]
                shap_values = shap_values[-1]
            shap_row = np.array(shap_values).reshape(-1)
        except Exception:
            return self._fallback_reasons(top_k)

        order = np.argsort(np.abs(shap_row))[::-1][:top_k]
        reasons = []
        for idx in order:
            name = self.feature_names_transformed[idx]
            desc = _map_transformed_name_to_raw(name)
            direction = "increasing" if shap_row[idx] > 0 else "decreasing"
            magnitude = abs(shap_row[idx])
            reasons.append(f"{desc.capitalize()} is {direction} the estimated forgetting risk (impact: {magnitude:.3f})")
        return reasons

    def explain_with_values(self, X_transformed_row: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Returns detailed explanation with SHAP values, feature names, and directions.
        Useful for programmatic analysis and detailed reporting.
        """
        if self._explainer is None:
            return self._fallback_reasons_with_values(top_k)

        try:
            shap_values = self._explainer.shap_values(X_transformed_row)
            if isinstance(shap_values, list):
                shap_values = shap_values[-1]
            shap_row = np.array(shap_values).reshape(-1)
        except Exception:
            return self._fallback_reasons_with_values(top_k)

        order = np.argsort(np.abs(shap_row))[::-1][:top_k]
        explanations = []
        for idx in order:
            name = self.feature_names_transformed[idx]
            desc = _map_transformed_name_to_raw(name)
            value = float(shap_row[idx])
            explanations.append({
                "feature": name,
                "description": desc,
                "shap_value": value,
                "direction": "increasing" if value > 0 else "decreasing",
                "magnitude": abs(value),
                "rank": len(explanations) + 1,
            })
        return explanations

    def get_global_importance(self, X_background: np.ndarray, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Compute global feature importance using SHAP values on background data.
        Returns sorted list of feature importances.
        """
        if self._explainer is None:
            return self._fallback_global_importance(top_k)

        try:
            shap_values = self._explainer.shap_values(X_background)
            if isinstance(shap_values, list):
                shap_values = shap_values[-1]
            shap_values = np.asarray(shap_values)
            
            # Compute mean absolute SHAP values
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
            
            order = np.argsort(mean_abs_shap)[::-1][:top_k]
            importances = []
            for idx in order:
                name = self.feature_names_transformed[idx]
                desc = _map_transformed_name_to_raw(name)
                importances.append({
                    "feature": name,
                    "description": desc,
                    "mean_abs_shap": float(mean_abs_shap[idx]),
                    "rank": len(importances) + 1,
                })
            return importances
        except Exception:
            return self._fallback_global_importance(top_k)

    def _fallback_reasons_with_values(self, top_k: int) -> List[Dict[str, Any]]:
        if hasattr(self.raw_model, "feature_importances_"):
            importances = self.raw_model.feature_importances_
        elif hasattr(self.raw_model, "coef_"):
            importances = np.abs(self.raw_model.coef_[0])
        else:
            return [{"error": "Explanation unavailable for this model type"}]

        order = np.argsort(importances)[::-1][:top_k]
        explanations = []
        for idx in order:
            name = self.feature_names_transformed[idx]
            desc = _map_transformed_name_to_raw(name)
            explanations.append({
                "feature": name,
                "description": desc,
                "importance": float(importances[idx]),
                "rank": len(explanations) + 1,
                "note": "Using global feature importance (SHAP unavailable)",
            })
        return explanations

    def _fallback_global_importance(self, top_k: int) -> List[Dict[str, Any]]:
        if hasattr(self.raw_model, "feature_importances_"):
            importances = self.raw_model.feature_importances_
        elif hasattr(self.raw_model, "coef_"):
            importances = np.abs(self.raw_model.coef_[0])
        else:
            return [{"error": "Global importance unavailable for this model type"}]

        order = np.argsort(importances)[::-1][:top_k]
        importances_list = []
        for idx in order:
            name = self.feature_names_transformed[idx]
            desc = _map_transformed_name_to_raw(name)
            importances_list.append({
                "feature": name,
                "description": desc,
                "importance": float(importances[idx]),
                "rank": len(importances_list) + 1,
                "note": "Using model native feature importance (SHAP unavailable)",
            })
        return importances_list

    def _fallback_reasons(self, top_k: int) -> List[str]:
        if hasattr(self.raw_model, "feature_importances_"):
            importances = self.raw_model.feature_importances_
        elif hasattr(self.raw_model, "coef_"):
            importances = np.abs(self.raw_model.coef_[0])
        else:
            return ["Explanation unavailable for this model type"]

        order = np.argsort(importances)[::-1][:top_k]
        reasons = []
        for idx in order:
            name = self.feature_names_transformed[idx]
            desc = _map_transformed_name_to_raw(name)
            reasons.append(f"{desc.capitalize()} is among the strongest general predictors of forgetting risk")
        return reasons
