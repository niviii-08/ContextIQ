"""
train.py

End-to-end training pipeline:
  1. Generate / load reproducible dataset (+metadata & fingerprint)
  2. Chronological train/val/test split with leakage assertions
  3. Time-series cross-validation on train+val for stability estimates
  4. Fit preprocessors (scaled for linear, unscaled for trees)
  5. Train Dummy (baseline), Logistic Regression, Random Forest, XGBoost
  6. Evaluate all on held-out test (chronological) via threshold-tuned metrics
  7. Select best model using multi-metric strategy (PR-AUC primary)
  8. Calibrate probabilities (isotonic / sigmoid, pick best Brier)
  9. Persist model bundle, preprocessor, feature metadata, SHAP artifacts
 10. Generate SHAP global importance, summary, individual example
 11. Produce markdown performance report + plots

Run:
    python -m ml.training.train
"""

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
try:
    from sklearn.frozen import FrozenEstimator
except ImportError:
    class FrozenEstimator:
        def __init__(self, estimator):
            self.estimator = estimator
        def fit(self, X, y=None, **fit_params):
            return self
        def predict(self, X):
            return self.estimator.predict(X)
        def predict_proba(self, X):
            return self.estimator.predict_proba(X)

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_LOCAL_DEPS = ROOT / "pydeps"
if _LOCAL_DEPS.exists():
    sys.path.insert(0, str(_LOCAL_DEPS))

from xgboost import XGBClassifier

from ml.features.feature_spec import DEFAULT_SPEC, FEATURE_DESCRIPTIONS
from ml.preprocessing.pipeline import build_preprocessor, get_output_feature_names
from ml.training.splits import (
    chronological_split, chronological_splits_summary, time_series_cv_splits,
)
from ml.training.config import (
    SEED, MODEL_VERSION, DATASET_VERSION,
    LogisticRegressionParams, RandomForestParams, XGBoostParams,
    THRESHOLD_TUNING, CALIBRATION_CONFIG, SHAP_CONFIG, DATASET_CONFIG, SPLIT_CONFIG,
)
from ml.evaluation.report import generate_report
from ml.evaluation.model_comparison import generate_model_selection_report
from ml.evaluation.calibration_analysis import (
    generate_calibration_report,
    plot_detailed_calibration,
    compare_calibration_methods,
)

DATASET_PATH = ROOT / "datasets" / "tasks_raw.csv"
DATASET_META_PATH = ROOT / "datasets" / "dataset_metadata.json"
ARTIFACTS_DIR = ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


def compute_metrics(y_true, y_pred, y_prob):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
        "specificity": float(tn / max(1, tn + fp)),
    }


def tune_threshold(y_val, val_prob, metric=None):
    if metric is None:
        metric = THRESHOLD_TUNING["metric"]
    thresholds = np.linspace(
        THRESHOLD_TUNING["min_threshold"],
        THRESHOLD_TUNING["max_threshold"],
        THRESHOLD_TUNING["n_thresholds"],
    )
    best_t, best_score = 0.5, -1
    for t in thresholds:
        preds = (val_prob >= t).astype(int)
        if metric == "f1":
            score = f1_score(y_val, preds, zero_division=0)
        elif metric == "recall":
            score = recall_score(y_val, preds, zero_division=0)
        elif metric == "precision":
            score = precision_score(y_val, preds, zero_division=0)
        else:
            score = accuracy_score(y_val, preds)
        if score > best_score:
            best_score = score
            best_t = t
    return float(best_t), float(best_score)


def _ensure_dataset():
    if not DATASET_PATH.exists() or not DATASET_META_PATH.exists():
        print("Dataset missing; generating reproducible synthetic dataset...")
        from ml.data.generate_dataset import main as gen_main
        gen_main()


def run_time_series_cv(train_val_df, build_model_fn, preprocessor_factory,
                        model_label="model", scale_numeric=False):
    cv_results = []
    for fold_idx, (cv_tr, cv_te) in enumerate(time_series_cv_splits(train_val_df)):
        pre = preprocessor_factory(scale_numeric=scale_numeric)
        feature_cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
        X_tr = pre.fit_transform(cv_tr[feature_cols])
        X_te = pre.transform(cv_te[feature_cols])
        y_tr = cv_tr[DEFAULT_SPEC.target].values
        y_te = cv_te[DEFAULT_SPEC.target].values
        model = build_model_fn(y_tr)
        model.fit(X_tr, y_tr)
        te_prob = model.predict_proba(X_te)[:, 1]
        t, _ = tune_threshold(y_te, te_prob)
        te_pred = (te_prob >= t).astype(int)
        m = compute_metrics(y_te, te_pred, te_prob)
        m["fold"] = fold_idx
        m["threshold"] = t
        clean = {}
        for k, v in m.items():
            if hasattr(v, "tolist"):
                clean[k] = v.tolist()
            elif isinstance(v, (np.integer,)):
                clean[k] = int(v)
            elif isinstance(v, (np.floating,)):
                clean[k] = float(v)
            else:
                clean[k] = v
        cv_results.append(clean)
    return cv_results


def _cv_summary(cv_results):
    if not cv_results:
        return {}
    keys = [k for k in cv_results[0].keys() if k not in ("confusion_matrix", "fold")]
    summary = {}
    for k in keys:
        vals = [float(r[k]) for r in cv_results if isinstance(r[k], (int, float))]
        if vals:
            summary[k] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "n_folds": len(vals),
            }
    summary["per_fold"] = cv_results
    return summary


def main():
    t0 = time.time()

    # Tests and deployment jobs may redirect artifact output to a fresh path.
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_dataset()

    with open(DATASET_META_PATH) as f:
        dataset_meta = json.load(f)

    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df)} rows (dataset fingerprint={dataset_meta.get('fingerprint_sha256_16','n/a')}).")

    class_balance = df[DEFAULT_SPEC.target].value_counts(normalize=True).to_dict()
    pos_rate = float(class_balance.get(1, class_balance.get("1", 0.28)))
    print(f"Class balance: pos={pos_rate:.3f} neg={1-pos_rate:.3f}")

    train_df, val_df, test_df = chronological_split(df)
    split_summary = chronological_splits_summary(train_df, val_df, test_df)
    print(f"Split sizes -> train: {len(train_df)}, val: {len(val_df)}, test: {len(test_df)}")
    print(f"Split dates: train={split_summary['train']['date_min']}..{split_summary['train']['date_max']}")

    feature_cols = DEFAULT_SPEC.categorical + DEFAULT_SPEC.numeric
    X_train_raw, y_train = train_df[feature_cols], train_df[DEFAULT_SPEC.target]
    X_val_raw, y_val = val_df[feature_cols], val_df[DEFAULT_SPEC.target]
    X_test_raw, y_test = test_df[feature_cols], test_df[DEFAULT_SPEC.target]

    train_val_df = pd.concat([train_df, val_df], axis=0, ignore_index=True)

    results = {}
    fitted_models = {}
    fitted_preprocessors = {}
    cv_summaries = {}

    # ---------------- Dummy baseline (predict most-frequent class) ----------------
    print("\n[1/4] Training Dummy baseline (most-frequent)...")
    pre_dum = build_preprocessor(scale_numeric=False)
    X_train_dum = pre_dum.fit_transform(X_train_raw)
    X_val_dum = pre_dum.transform(X_val_raw)
    X_test_dum = pre_dum.transform(X_test_raw)
    dum = DummyClassifier(strategy="most_frequent", random_state=SEED)
    dum.fit(X_train_dum, y_train)
    dum_val_prob = dum.predict_proba(X_val_dum)[:, 1]
    dum_test_prob = dum.predict_proba(X_test_dum)[:, 1]
    dum_test_pred = (dum_test_prob >= 0.5).astype(int)
    results["dummy_most_frequent"] = compute_metrics(y_test.values, dum_test_pred, dum_test_prob)
    results["dummy_most_frequent"]["threshold"] = 0.5
    results["dummy_most_frequent"]["params"] = {"strategy": "most_frequent"}
    fitted_models["dummy_most_frequent"] = dum
    fitted_preprocessors["dummy_most_frequent"] = pre_dum

    def _build_lr(y):
        p = LogisticRegressionParams()
        return LogisticRegression(**p.to_dict())

    print("\n[2/4] Training Logistic Regression baseline...")
    pre_lr = build_preprocessor(scale_numeric=True)
    X_train_lr = pre_lr.fit_transform(X_train_raw)
    X_val_lr = pre_lr.transform(X_val_raw)
    X_test_lr = pre_lr.transform(X_test_raw)
    lr_params = LogisticRegressionParams()
    lr = LogisticRegression(**lr_params.to_dict())
    lr.fit(X_train_lr, y_train)
    lr_val_prob = lr.predict_proba(X_val_lr)[:, 1]
    lr_test_prob = lr.predict_proba(X_test_lr)[:, 1]
    lr_thresh, _ = tune_threshold(y_val.values, lr_val_prob)
    lr_test_pred = (lr_test_prob >= lr_thresh).astype(int)
    results["logistic_regression"] = compute_metrics(y_test.values, lr_test_pred, lr_test_prob)
    results["logistic_regression"]["threshold"] = lr_thresh
    results["logistic_regression"]["params"] = lr_params.to_dict()
    fitted_models["logistic_regression"] = lr
    fitted_preprocessors["logistic_regression"] = pre_lr
    print("  Running time-series CV (5-fold walk-forward)...")
    cv_summaries["logistic_regression"] = _cv_summary(
        run_time_series_cv(train_val_df, _build_lr, build_preprocessor,
                          "logistic_regression", scale_numeric=True)
    )

    def _build_rf(y):
        p = RandomForestParams()
        return RandomForestClassifier(**p.to_dict())

    print("\n[3/4] Training Random Forest...")
    pre_rf = build_preprocessor(scale_numeric=False)
    X_train_rf = pre_rf.fit_transform(X_train_raw)
    X_val_rf = pre_rf.transform(X_val_raw)
    X_test_rf = pre_rf.transform(X_test_raw)
    rf_params = RandomForestParams()
    rf = RandomForestClassifier(**rf_params.to_dict())
    rf.fit(X_train_rf, y_train)
    rf_val_prob = rf.predict_proba(X_val_rf)[:, 1]
    rf_test_prob = rf.predict_proba(X_test_rf)[:, 1]
    rf_thresh, _ = tune_threshold(y_val.values, rf_val_prob)
    rf_test_pred = (rf_test_prob >= rf_thresh).astype(int)
    results["random_forest"] = compute_metrics(y_test.values, rf_test_pred, rf_test_prob)
    results["random_forest"]["threshold"] = rf_thresh
    results["random_forest"]["params"] = rf_params.to_dict()
    fitted_models["random_forest"] = rf
    fitted_preprocessors["random_forest"] = pre_rf
    print("  Running time-series CV (5-fold walk-forward)...")
    cv_summaries["random_forest"] = _cv_summary(
        run_time_series_cv(train_val_df, _build_rf, build_preprocessor,
                          "random_forest", scale_numeric=False)
    )

    def _build_xgb(y):
        p = XGBoostParams()
        spw = float((y == 0).sum() / max(1, (y == 1).sum()))
        d = p.to_dict()
        d["scale_pos_weight"] = spw
        return XGBClassifier(**d)

    print("\n[4/4] Training XGBoost...")
    pre_xgb = build_preprocessor(scale_numeric=False)
    X_train_xgb = pre_xgb.fit_transform(X_train_raw)
    X_val_xgb = pre_xgb.transform(X_val_raw)
    X_test_xgb = pre_xgb.transform(X_test_raw)
    xgb_params = XGBoostParams()
    scale_pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    xgb_dict = xgb_params.to_dict()
    xgb_dict["scale_pos_weight"] = scale_pos_weight
    xgb = XGBClassifier(**xgb_dict)
    xgb.fit(X_train_xgb, y_train)
    xgb_val_prob = xgb.predict_proba(X_val_xgb)[:, 1]
    xgb_test_prob = xgb.predict_proba(X_test_xgb)[:, 1]
    xgb_thresh, _ = tune_threshold(y_val.values, xgb_val_prob)
    xgb_test_pred = (xgb_test_prob >= xgb_thresh).astype(int)
    results["xgboost"] = compute_metrics(y_test.values, xgb_test_pred, xgb_test_prob)
    results["xgboost"]["threshold"] = xgb_thresh
    results["xgboost"]["params"] = dict(xgb_dict)
    results["xgboost"]["params"]["scale_pos_weight"] = scale_pos_weight
    fitted_models["xgboost"] = xgb
    fitted_preprocessors["xgboost"] = pre_xgb
    print("  Running time-series CV (5-fold walk-forward)...")
    cv_summaries["xgboost"] = _cv_summary(
        run_time_series_cv(train_val_df, _build_xgb, build_preprocessor,
                          "xgboost", scale_numeric=False)
    )

    # ---------------- Model selection ----------------
    print("\n--- Model selection ---")

    def selection_key(name):
        if name == "dummy_most_frequent":
            return (-1.0, -1.0, -1.0)
        m = results[name]
        return (float(m["pr_auc"]), float(m["roc_auc"]), float(m["f1"]))

    ranked = sorted(results.keys(), key=selection_key, reverse=True)
    best_model_name = ranked[0]
    print("Candidates (ranked by PR-AUC > ROC-AUC > F1):")
    for i, n in enumerate(ranked):
        m = results[n]
        line = (
            f"  {i+1}. {n}: PR-AUC={m.get('pr_auc',-1):.4f} "
            f"ROC-AUC={m.get('roc_auc',-1):.4f} F1={m.get('f1',-1):.4f} ACC={m.get('accuracy',-1):.4f}"
        )
        print(line)
    print(f"Selected model: {best_model_name}")
    print(json.dumps(results[best_model_name], indent=2, default=str))

    best_model = fitted_models[best_model_name]
    best_preprocessor = fitted_preprocessors[best_model_name]

    def _transformed_for(name):
        return {
            "dummy_most_frequent": (X_val_dum, X_test_dum),
            "logistic_regression": (X_val_lr, X_test_lr),
            "random_forest": (X_val_rf, X_test_rf),
            "xgboost": (X_val_xgb, X_test_xgb),
        }[name]

    X_val_sel, X_test_sel = _transformed_for(best_model_name)

    # ---------------- Probability calibration ----------------
    print(f"\nCalibrating {best_model_name} probabilities...")
    cal_results = {}
    best_cal_method = None
    best_cal_model = None
    brier_best = float("inf")
    frozen = FrozenEstimator(best_model)
    for method in CALIBRATION_CONFIG["methods"]:
        try:
            cal = CalibratedClassifierCV(frozen, method=method, cv="prefit")
            cal.fit(X_val_sel, y_val.values)
            cal_val_prob = cal.predict_proba(X_val_sel)[:, 1]
            cal_test_prob = cal.predict_proba(X_test_sel)[:, 1]
            brier_val = brier_score_loss(y_val.values, cal_val_prob)
            brier_test = brier_score_loss(y_test.values, cal_test_prob)
            cal_results[method] = {
                "brier_val": float(brier_val),
                "brier_test": float(brier_test),
            }
            if brier_val < brier_best:
                brier_best = brier_val
                best_cal_method = method
                best_cal_model = cal
        except Exception as e:
            cal_results[method] = {"error": str(e)}

    uncal_test_prob = best_model.predict_proba(X_test_sel)[:, 1]
    uncal_val_prob = best_model.predict_proba(X_val_sel)[:, 1]
    brier_uncal_val = brier_score_loss(y_val.values, uncal_val_prob)
    brier_uncal_test = brier_score_loss(y_test.values, uncal_test_prob)

    use_calibrated = (best_cal_model is not None) and (brier_best < brier_uncal_val)
    if use_calibrated:
        final_model = best_cal_model
        final_test_prob = best_cal_model.predict_proba(X_test_sel)[:, 1]
        final_val_prob = best_cal_model.predict_proba(X_val_sel)[:, 1]
        calibration_method_used = best_cal_method
    else:
        final_model = best_model
        final_test_prob = uncal_test_prob
        final_val_prob = uncal_val_prob
        calibration_method_used = None

    print(f"Uncalibrated Brier (val) = {brier_uncal_val:.4f}")
    for method, r in cal_results.items():
        if "brier_val" in r:
            print(f"  {method}: Brier(val)={r['brier_val']:.4f} Brier(test)={r['brier_test']:.4f}")
    print(f"Use calibrated: {use_calibrated} (method={calibration_method_used})")

    best_thresh, _ = tune_threshold(y_val.values, final_val_prob)
    final_test_pred = (final_test_prob >= best_thresh).astype(int)
    final_metrics = compute_metrics(y_test.values, final_test_pred, final_test_prob)
    final_metrics["threshold"] = best_thresh
    final_metrics["calibration_applied"] = bool(use_calibrated)
    final_metrics["calibration_method"] = calibration_method_used
    final_metrics["brier_uncalibrated_val"] = float(brier_uncal_val)
    final_metrics["brier_uncalibrated_test"] = float(brier_uncal_test)
    if use_calibrated:
        final_metrics["brier_calibrated_val"] = float(brier_best)
    final_metrics["calibration_comparison"] = cal_results

    # ---------------- Feature metadata ----------------
    feature_names_out = get_output_feature_names(best_preprocessor)

    num_pipeline = best_preprocessor.named_transformers_.get("num")
    cat_pipeline = best_preprocessor.named_transformers_.get("cat")
    numeric_medians = None
    num_means = None
    num_scales = None
    if num_pipeline is not None:
        imp = num_pipeline.named_steps.get("imputer")
        if imp is not None and hasattr(imp, "statistics_"):
            numeric_medians = dict(zip(DEFAULT_SPEC.numeric, [float(x) for x in imp.statistics_]))
        scl = num_pipeline.named_steps.get("scaler")
        if scl is not None and hasattr(scl, "mean_"):
            num_means = dict(zip(DEFAULT_SPEC.numeric, [float(x) for x in scl.mean_]))
            num_scales = dict(zip(DEFAULT_SPEC.numeric, [float(x) for x in scl.scale_]))

    cat_most_freq = None
    cat_categories = None
    if cat_pipeline is not None:
        imp = cat_pipeline.named_steps.get("imputer")
        if imp is not None and hasattr(imp, "statistics_"):
            cat_most_freq = dict(zip(DEFAULT_SPEC.categorical, [str(x) for x in imp.statistics_]))
        oh = cat_pipeline.named_steps.get("onehot")
        if oh is not None and hasattr(oh, "categories_"):
            cat_categories = {}
            for name, cats in zip(DEFAULT_SPEC.categorical, oh.categories_):
                cat_categories[name] = [str(c) for c in cats]

    feature_metadata = {
        "model_version": MODEL_VERSION,
        "dataset_version": dataset_meta.get("dataset_version", DATASET_VERSION),
        "dataset_fingerprint": dataset_meta.get("fingerprint_sha256_16"),
        "selected_model": best_model_name,
        "raw_categorical_features": DEFAULT_SPEC.categorical,
        "raw_numeric_features": DEFAULT_SPEC.numeric,
        "target": DEFAULT_SPEC.target,
        "transformed_feature_names": feature_names_out,
        "n_transformed_features": len(feature_names_out),
        "preprocessor": {
            "numeric_impute_medians": numeric_medians,
            "numeric_standard_scaler_means": num_means,
            "numeric_standard_scaler_scales": num_scales,
            "categorical_impute_most_frequent": cat_most_freq,
            "categorical_onehot_categories": cat_categories,
        },
        "feature_descriptions": FEATURE_DESCRIPTIONS,
        "generated_at_unix": time.time(),
    }
    with open(ARTIFACTS_DIR / "feature_metadata.json", "w") as f:
        json.dump(feature_metadata, f, indent=2, default=str)

    # SHAP background sample
    background_sample = None
    if best_model_name == "logistic_regression":
        n_bg = min(SHAP_CONFIG["n_background_samples"], X_train_lr.shape[0])
        bg_idx = np.random.RandomState(SEED).choice(X_train_lr.shape[0], size=n_bg, replace=False)
        background_sample = X_train_lr[bg_idx]
        if hasattr(background_sample, "toarray"):
            background_sample = background_sample.toarray()

    # ---------------- Persist model bundle ----------------
    model_bundle = {
        "model": final_model,
        "raw_model": best_model,
        "preprocessor": best_preprocessor,
        "model_name": best_model_name,
        "model_version": MODEL_VERSION,
        "threshold": best_thresh,
        "calibrated": use_calibrated,
        "calibration_method": calibration_method_used,
        "feature_names_raw": feature_cols,
        "feature_names_transformed": feature_names_out,
        "categorical_features": DEFAULT_SPEC.categorical,
        "numeric_features": DEFAULT_SPEC.numeric,
        "background_sample": background_sample,
    }
    joblib.dump(model_bundle, ARTIFACTS_DIR / "model_bundle.joblib")
    print(f"Saved model bundle to {ARTIFACTS_DIR / 'model_bundle.joblib'}")

    # ---------------- Full metrics JSON ----------------
    baseline_acc = max(1 - pos_rate, pos_rate)
    all_metrics = {
        "model_version": MODEL_VERSION,
        "dataset_version": dataset_meta.get("dataset_version", DATASET_VERSION),
        "dataset_fingerprint": dataset_meta.get("fingerprint_sha256_16"),
        "seed": SEED,
        "selected_model": best_model_name,
        "primary_justification": (
            "Model selection is driven primarily by PR-AUC (Average Precision) because "
            "for forgetting-risk prediction — a class-imbalanced problem where the "
            "positive class (forgotten) is the minority and the cost of missing a "
            "forgotten task (false negative) is high for the user. ROC-AUC is a "
            "secondary tie-breaker for ranking quality, and F1 confirms thresholded "
            "quality. Accuracy is intentionally de-prioritized because a trivial "
            f"'never-forget' majority-class classifier achieves ~{100*baseline_acc:.1f}% "
            "accuracy by doing nothing useful."
        ),
        "class_balance": {str(k): float(v) for k, v in class_balance.items()},
        "split_summary": split_summary,
        "split_config": SPLIT_CONFIG,
        "cv_config": {
            "strategy": "walk-forward_time_series",
            "n_splits": 5,
        },
        "candidate_metrics_test": results,
        "time_series_cv": cv_summaries,
        "final_selected_metrics": final_metrics,
        "threshold_tuning": THRESHOLD_TUNING,
        "calibration": {
            "methods_tried": CALIBRATION_CONFIG["methods"],
            "applied": bool(use_calibrated),
            "method": calibration_method_used,
        },
        "trained_at_unix": time.time(),
        "training_duration_seconds": round(time.time() - t0, 1),
    }
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)

    # ---------------- SHAP + plots + report ----------------
    print("\nGenerating evaluation report (plots, SHAP)...")

    X_shap_background = None
    if best_model_name in ("random_forest", "xgboost"):
        X_shap_background = {"random_forest": X_train_rf, "xgboost": X_train_xgb}[best_model_name]
        if hasattr(X_shap_background, "toarray"):
            X_shap_background = X_shap_background.toarray()
        n_sum = min(SHAP_CONFIG["n_summary_samples"], X_shap_background.shape[0])
        bg_idx_shap = np.random.RandomState(SEED).choice(X_shap_background.shape[0], size=n_sum, replace=False)
        X_shap_background = X_shap_background[bg_idx_shap]
    elif best_model_name == "logistic_regression":
        X_shap_background = background_sample

    X_test_for_plots = X_test_sel
    if hasattr(X_test_for_plots, "toarray"):
        X_test_for_plots = X_test_for_plots.toarray()

    # Pick 3 test-set indices for individual SHAP examples (low, mid, high probability)
    sort_idx = np.argsort(final_test_prob)
    n_te = len(final_test_prob)
    example_indices = [sort_idx[0], sort_idx[n_te // 2], sort_idx[-1]]
    X_examples = X_test_for_plots[example_indices]
    y_examples_true = y_test.values[example_indices]
    y_examples_prob = final_test_prob[example_indices]

    generate_report(
        y_test=y_test.values,
        final_test_prob=final_test_prob,
        final_test_pred=final_test_pred,
        candidates_prob={
            "dummy_most_frequent": dum_test_prob,
            "logistic_regression": lr_test_prob,
            "random_forest": rf_test_prob,
            "xgboost": xgb_test_prob,
        },
        y_test_for_candidates=y_test.values,
        best_model=best_model,
        preprocessor=best_preprocessor,
        feature_names=feature_names_out,
        X_test_transformed=X_test_for_plots,
        best_model_name=best_model_name,
        artifacts_dir=ARTIFACTS_DIR,
        shap_background=X_shap_background,
        raw_model=best_model,
        final_metrics=final_metrics,
        all_metrics_dict=all_metrics,
        X_examples=X_examples,
        example_true_labels=y_examples_true,
        example_probabilities=y_examples_prob,
        example_indices=example_indices,
    )

    print("  Generating model selection comparison report...")
    generate_model_selection_report(
        all_metrics=all_metrics,
        cv_summaries=cv_summaries,
        artifacts_dir=ARTIFACTS_DIR,
    )

    print("  Generating detailed calibration analysis...")
    # Collect all model probabilities for calibration comparison
    all_probabilities = {
        "dummy_most_frequent": dum_test_prob,
        "logistic_regression": lr_test_prob,
        "random_forest": rf_test_prob,
        "xgboost": xgb_test_prob,
        f"{best_model_name}_calibrated": final_test_prob,
    }
    
    generate_calibration_report(
        y_true=y_test.values,
        model_probabilities=all_probabilities,
        artifacts_dir=ARTIFACTS_DIR,
    )
    
    # Generate detailed calibration plot for final model
    plot_detailed_calibration(
        y_true=y_test.values,
        y_prob=final_test_prob,
        model_name=f"{best_model_name} (final)",
        out_path=ARTIFACTS_DIR / "calibration_detailed.png",
    )
    
    # Generate calibration comparison plot
    compare_calibration_methods(
        y_true=y_test.values,
        probabilities=all_probabilities,
        out_path=ARTIFACTS_DIR / "calibration_comparison.png",
    )

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Artifacts saved to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
