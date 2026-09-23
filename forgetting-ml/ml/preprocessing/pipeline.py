"""
pipeline.py

Builds the shared sklearn ColumnTransformer used to preprocess raw feature
rows into model-ready numeric matrices. The SAME fitted preprocessor object
is serialized and reused at inference time to guarantee train/serve
consistency.
"""

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from ml.features.feature_spec import DEFAULT_SPEC


def build_preprocessor(scale_numeric: bool = True) -> ColumnTransformer:
    """
    Returns an unfitted ColumnTransformer.

    scale_numeric=True is used for the Logistic Regression baseline (which
    benefits from standardized inputs). Tree models (RF / XGBoost) do not
    require scaling, but we still route numeric features through an
    imputer for robustness against missing values at inference time. A
    single shared transformer definition keeps the two paths consistent
    in every respect other than the scaling step.
    """
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, DEFAULT_SPEC.numeric),
            ("cat", categorical_pipeline, DEFAULT_SPEC.categorical),
        ],
        remainder="drop",
    )
    return preprocessor


def get_output_feature_names(preprocessor: ColumnTransformer):
    """Returns the flat list of feature names after transformation, in order."""
    return list(preprocessor.get_feature_names_out())
