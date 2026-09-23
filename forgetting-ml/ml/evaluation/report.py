"""
report.py

Generates the model evaluation report artifacts:
  - confusion_matrix.png
  - roc_curve.png
  - precision_recall_curve.png
  - feature_importance.png
  - calibration_plot.png
  - shap_summary_bar.png         (global SHAP: mean |SHAP| bar)
  - shap_beeswarm.png            (global SHAP: beeswarm / summary)
  - shap_individual_waterfalls.png (3 individual predictions explained)
  - performance_report.md        (human-readable report)

All figures are computed from actual model outputs on the held-out
chronological test set - no numbers are invented.
"""

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay,
    confusion_matrix, precision_recall_curve, roc_curve,
)

warnings.filterwarnings("ignore")


def _save(fig, path, dpi=150):
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_matrix(y_true, y_pred, out_path):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(5, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Not Forgotten", "Forgotten"])
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix (Selected Model, Test Set)")
    _save(fig, out_path)


def plot_roc_curve(candidates_prob, y_true, out_path):
    fig, ax = plt.subplots(figsize=(6, 6))
    for name, prob in candidates_prob.items():
        fpr, tpr, _ = roc_curve(y_true, prob)
        ax.plot(fpr, tpr, label=name)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — All Candidate Models (Test Set)")
    ax.legend(fontsize=8)
    _save(fig, out_path)


def plot_pr_curve(candidates_prob, y_true, out_path):
    fig, ax = plt.subplots(figsize=(6, 6))
    for name, prob in candidates_prob.items():
        precision, recall, _ = precision_recall_curve(y_true, prob)
        ax.plot(recall, precision, label=name)
    baseline = float(np.mean(y_true))
    ax.axhline(baseline, linestyle="--", color="gray", label=f"Baseline ({baseline:.2f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve — All Candidate Models (Test Set)")
    ax.legend(fontsize=8)
    _save(fig, out_path)


def plot_feature_importance(best_model, feature_names, best_model_name, out_path):
    fig, ax = plt.subplots(figsize=(9, 7))

    importances = None
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
    elif hasattr(best_model, "coef_"):
        importances = np.abs(best_model.coef_[0])

    if importances is None:
        ax.text(0.5, 0.5, "Feature importance not available for this model type",
                ha="center", va="center")
    else:
        order = np.argsort(importances)[::-1][:20]
        names = np.array(feature_names)[order]
        vals = importances[order]
        ax.barh(range(len(vals)), vals[::-1], color="#4C78A8")
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(names[::-1], fontsize=8)
        ax.set_xlabel("Importance (MDI / |coef|)")
        ax.set_title(f"Top Feature Importances — {best_model_name} (20 features max)")

    _save(fig, out_path)


def plot_calibration(y_true, prob, out_path):
    fig, ax = plt.subplots(figsize=(6, 6))
    try:
        frac_pos, mean_pred = calibration_curve(y_true, prob, n_bins=10, strategy="quantile")
        ax.plot(mean_pred, frac_pos, marker="o", label="Selected model", color="#4C78A8")
    except Exception:
        pass
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly calibrated")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Calibration Plot (Test Set)")
    ax.legend()
    _save(fig, out_path)


def _shorten_names(names: List[str], max_len: int = 40) -> List[str]:
    out = []
    for n in names:
        if len(n) > max_len:
            out.append(n[: max_len - 3] + "...")
        else:
            out.append(n)
    return out


def plot_shap_global(raw_model, model_name, X_shap_background, X_test_transformed,
                      feature_names, artifacts_dir, shap_config_top_k: int = 20):
    try:
        import shap
    except ImportError:
        print("shap not installed; skipping SHAP plots")
        return

    if X_shap_background is None or X_test_transformed is None:
        return

    try:
        if model_name in ("random_forest", "xgboost"):
            explainer = shap.TreeExplainer(raw_model)
        elif model_name == "logistic_regression":
            bg = X_shap_background
            if bg is None:
                return
            explainer = shap.LinearExplainer(raw_model, bg, feature_perturbation="interventional")
        else:
            return
    except Exception as e:
        print(f"SHAP explainer construction failed: {e}")
        return

    try:
        sv = explainer.shap_values(X_test_transformed)
        if isinstance(sv, list):
            sv = sv[-1]
        sv = np.asarray(sv)
    except Exception as e:
        print(f"SHAP value computation failed: {e}")
        return

    short_names = _shorten_names(feature_names, max_len=50)
    top_k = min(shap_config_top_k, len(feature_names))

    try:
        mean_abs = np.mean(np.abs(sv), axis=0)
        order = np.argsort(mean_abs)[::-1][:top_k]
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(range(len(order)), mean_abs[order][::-1], color="#F58518")
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([short_names[i] for i in order[::-1]], fontsize=8)
        ax.set_xlabel("mean(|SHAP value|)")
        ax.set_title(f"SHAP Global Feature Importance (Top {len(order)})")
        _save(fig, artifacts_dir / "shap_summary_bar.png")
    except Exception as e:
        print(f"SHAP bar plot failed: {e}")

    try:
        fig, ax = plt.subplots(figsize=(10, 7))
        order_top = np.argsort(np.mean(np.abs(sv), axis=0))[::-1][:top_k]
        sv_top = sv[:, order_top]
        fn_top = [short_names[i] for i in order_top]

        for i in range(sv_top.shape[1] - 1, -1, -1):
            col = sv_top[:, i]
            xs = col
            ys = np.full_like(xs, fill_value=float(i))
            order_xs = np.argsort(xs)
            jitter = np.random.RandomState(42).uniform(-0.35, 0.35, size=len(xs))
            ys_j = ys + jitter
            ax.scatter(xs[order_xs], ys_j[order_xs], s=6, alpha=0.55, c="#4C78A8", linewidths=0)
        ax.set_yticks(range(len(fn_top)))
        ax.set_yticklabels(fn_top, fontsize=8)
        ax.axvline(0.0, linestyle="--", color="gray", linewidth=0.8)
        ax.set_xlabel("SHAP value (impact on predicted forgetting probability)")
        ax.set_title(f"SHAP Beeswarm Summary (Top {len(fn_top)} features, Test Set)")
        _save(fig, artifacts_dir / "shap_beeswarm.png")
    except Exception as e:
        print(f"SHAP beeswarm plot failed: {e}")


def plot_shap_individual(raw_model, model_name, X_shap_background, X_examples,
                          example_probabilities, example_true_labels,
                          feature_names, artifacts_dir):
    try:
        import shap
    except ImportError:
        return

    if X_shap_background is None or X_examples is None:
        return

    try:
        if model_name in ("random_forest", "xgboost"):
            explainer = shap.TreeExplainer(raw_model)
        elif model_name == "logistic_regression":
            if X_shap_background is None:
                return
            explainer = shap.LinearExplainer(raw_model, X_shap_background, feature_perturbation="interventional")
        else:
            return
    except Exception as e:
        print(f"SHAP individual explainer build failed: {e}")
        return

    short_names = _shorten_names(feature_names, max_len=50)

    n_examples = len(X_examples)
    if n_examples == 0:
        return
    n_cols = min(n_examples, 3)
    fig, axes = plt.subplots(1, n_cols, figsize=(5.2 * n_cols, 5))
    if n_cols == 1:
        axes = [axes]

    tags = []
    for i in range(n_examples):
        if i == 0:
            tags.append("LOW-risk example")
        elif i == n_examples - 1:
            tags.append("HIGH-risk example")
        else:
            tags.append("MEDIUM-risk example")

    for idx in range(n_cols):
        ax = axes[idx]
        X_row = X_examples[idx:idx + 1]
        try:
            sv = explainer.shap_values(X_row)
            if isinstance(sv, list):
                sv = sv[-1]
            sv = np.asarray(sv).reshape(-1)
        except Exception as e:
            ax.text(0.5, 0.5, f"SHAP failed: {e}", ha="center", va="center", fontsize=8)
            ax.set_axis_off()
            continue

        top_k = min(10, len(sv))
        order = np.argsort(np.abs(sv))[::-1][:top_k]
        vals = sv[order]
        names = [short_names[i] for i in order]

        colors = ["#E45756" if v > 0 else "#4C78A8" for v in vals[::-1]]
        ax.barh(range(len(vals)), vals[::-1], color=colors)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(names[::-1], fontsize=7)
        ax.axvline(0.0, linestyle="--", color="gray", linewidth=0.6)
        p = example_probabilities[idx] if idx < len(example_probabilities) else float("nan")
        t = example_true_labels[idx] if idx < len(example_true_labels) else -1
        title = f"{tags[idx]}\np={p:.3f}  true={int(t)}"
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("SHAP value")

    fig.suptitle("SHAP Individual Prediction Explanations (Waterfall-like)", fontsize=11)
    _save(fig, artifacts_dir / "shap_individual_waterfalls.png", dpi=150)


def _fmt_pct(x):
    if x is None:
        return "N/A"
    return f"{100 * float(x):.2f}%"


def _fmt_num(x, decimals=4):
    if x is None:
        return "N/A"
    return f"{float(x):.{decimals}f}"


def write_markdown_report(final_metrics: Dict[str, Any], all_metrics_dict: Dict[str, Any],
                           candidates_prob: Dict[str, Any],
                           y_test: np.ndarray,
                           artifacts_dir: Path):
    lines: List[str] = []
    lines.append("# Forgetting-Risk Prediction — Performance Report")
    lines.append("")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")

    mv = all_metrics_dict.get("model_version", "?")
    dv = all_metrics_dict.get("dataset_version", "?")
    fp = all_metrics_dict.get("dataset_fingerprint", "?")
    sm = all_metrics_dict.get("selected_model", "?")
    dur = all_metrics_dict.get("training_duration_seconds", "?")
    lines.append("## Run Metadata")
    lines.append("")
    lines.append(f"- **Model version:** `{mv}`")
    lines.append(f"- **Dataset version:** `{dv}`")
    lines.append(f"- **Dataset fingerprint (SHA-256, 16):** `{fp}`")
    lines.append(f"- **Selected model:** `{sm}`")
    lines.append(f"- **Training duration:** {dur}s")
    lines.append("")

    just = all_metrics_dict.get("primary_justification", "")
    lines.append("## Which Metric Matters and Why")
    lines.append("")
    lines.append(just)
    lines.append("")
    lines.append("Concretely:")
    lines.append("")
    lines.append("- **PR-AUC (Average Precision)** ← PRIMARY. Summarizes the whole precision/recall trade-off curve; invariant to class imbalance and directly rewards ranking the *riskiest* tasks first.")
    lines.append("- **ROC-AUC** ← SECONDARY tie-breaker. Measures overall ranking discriminative power across all operating points.")
    lines.append("- **F1** ← tertiary. Quality of the chosen *operating threshold* (after threshold tuning on val).")
    lines.append("- **Recall** ← operational safety net. The fraction of actually-forgotten tasks that were flagged.")
    lines.append("- **Precision** ← operational trust. Fraction of flagged tasks that actually were forgotten.")
    lines.append("- **Accuracy** ← intentionally de-prioritized; misleading under class imbalance.")
    lines.append("")

    lines.append("## Class Balance")
    lines.append("")
    cb = all_metrics_dict.get("class_balance", {})
    lines.append(f"- Positive (forgotten=1): `{_fmt_pct(cb.get('1', cb.get(1, 0.0)))}`")
    lines.append(f"- Negative (forgotten=0): `{_fmt_pct(cb.get('0', cb.get(0, 0.0)))}`")
    lines.append("")

    lines.append("## Chronological Split Summary")
    lines.append("")
    ss = all_metrics_dict.get("split_summary", {})
    lines.append("| Split | N rows | N users | Date range | Forget rate |")
    lines.append("|-------|--------|---------|------------|-------------|")
    for k in ("train", "val", "test"):
        s = ss.get(k, {})
        rng = f"{s.get('date_min','?')} → {s.get('date_max','?')}"
        lines.append(
            f"| {k} | {s.get('n_rows','?')} | {s.get('n_users','?')} | {rng} | "
            f"{_fmt_pct(s.get('forget_rate'))} |"
        )
    lines.append("")
    lines.append("> Split rule: global chronological by date. 70% train / 15% val / 15% test.")
    lines.append("> A user may appear in all three splits but *always* with behaviour strictly later in val/test than in train (no time leakage).")
    lines.append("")

    lines.append("## Candidate Models — Held-Out Test Metrics")
    lines.append("")
    cand = all_metrics_dict.get("candidate_metrics_test", {})
    lines.append("| Model | Acc | Precision | Recall | F1 | ROC-AUC | **PR-AUC** | Brier |")
    lines.append("|-------|-----|-----------|--------|----|---------|------------|-------|")
    for name, m in cand.items():
        bold = "**" if name == sm else ""
        lines.append(
            f"| {bold}{name}{bold} | "
            f"{_fmt_num(m.get('accuracy'), 3)} | "
            f"{_fmt_num(m.get('precision'), 3)} | "
            f"{_fmt_num(m.get('recall'), 3)} | "
            f"{_fmt_num(m.get('f1'), 3)} | "
            f"{_fmt_num(m.get('roc_auc'), 3)} | "
            f"{bold}{_fmt_num(m.get('pr_auc'), 3)}{bold} | "
            f"{_fmt_num(m.get('brier_score'), 3)} |"
        )
    lines.append("")

    lines.append(f"## Final Selected Model: `{sm}`")
    lines.append("")
    fm = final_metrics
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for k in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "brier_score", "specificity"):
        lines.append(f"| {k} | {_fmt_num(fm.get(k), 4)} |")
    lines.append(f"| threshold (max F1 on val, post-calibration) | {_fmt_num(fm.get('threshold'), 3)} |")
    lines.append(f"| calibration applied? | {fm.get('calibration_applied')} ({fm.get('calibration_method','-')}) |")
    lines.append("")
    cm = fm.get("confusion_matrix", [[None, None], [None, None]])
    lines.append("### Confusion Matrix (selected model, test)")
    lines.append("")
    lines.append("| | Predicted Not Forgotten | Predicted Forgotten |")
    lines.append("|---|--------------------------|----------------------|")
    lines.append(f"| Actual Not Forgotten | **{cm[0][0]}** (TN) | {cm[0][1]} (FP) |")
    lines.append(f"| Actual Forgotten     | {cm[1][0]} (FN) | **{cm[1][1]}** (TP) |")
    lines.append("")

    lines.append("## Time-Series Cross-Validation (walk-forward, 5 folds on train+val)")
    lines.append("")
    cv = all_metrics_dict.get("time_series_cv", {})
    if cv:
        lines.append("| Model | Fold | PR-AUC ± std | ROC-AUC ± std | F1 ± std |")
        lines.append("|-------|------|--------------|---------------|----------|")
        for m_name, s in cv.items():
            nf = s.get("pr_auc", {}).get("n_folds", "?")
            pra = s.get("pr_auc", {})
            roc = s.get("roc_auc", {})
            f1 = s.get("f1", {})
            pra_s = f"{pra.get('mean', float('nan')):.4f} ± {pra.get('std', float('nan')):.4f}" if pra else "N/A"
            roc_s = f"{roc.get('mean', float('nan')):.4f} ± {roc.get('std', float('nan')):.4f}" if roc else "N/A"
            f1_s = f"{f1.get('mean', float('nan')):.4f} ± {f1.get('std', float('nan')):.4f}" if f1 else "N/A"
            lines.append(f"| {m_name} | {nf} | {pra_s} | {roc_s} | {f1_s} |")
        lines.append("")
        lines.append("> Walk-forward time-series CV avoids standard (shuffled) K-fold which is known to leak future information in sequential/behavioral data. Each CV fold is a strictly later date window than its train portion.")
    else:
        lines.append("_CV not run._")
    lines.append("")

    lines.append("## Probability Calibration")
    lines.append("")
    cal = all_metrics_dict.get("calibration", {})
    lines.append(f"- Methods evaluated: {cal.get('methods_tried', [])}")
    lines.append(f"- Calibration applied? {cal.get('applied')}")
    lines.append(f"- Chosen method: {cal.get('method')}")
    lines.append("")
    lines.append("## Class Imbalance Handling")
    lines.append("")
    lines.append("- **Training-time weighting:** LR/RF use `class_weight='balanced'` / `'balanced_subsample'`. XGBoost uses `scale_pos_weight = #neg/#pos`.")
    lines.append("- **Inference-time threshold tuning:** operating threshold is chosen to MAXIMIZE F1 on the validation split, rather than naively using 0.5. This is especially impactful under imbalance.")
    lines.append("- **Model selection metric:** PR-AUC (Average Precision) rather than accuracy, so that a 'trivial' majority-class baseline cannot look good by doing nothing.")
    lines.append("")

    lines.append("## Feature Metadata")
    lines.append("")
    lines.append("See `artifacts/feature_metadata.json` for the full contract: per-feature median imputation values, StandardScaler means/scales (for LR path), one-hot category lists, and human-readable descriptions.")
    lines.append("")

    lines.append("## Target-Leakage Prevention")
    lines.append("")
    lines.append("1. **Feature construction** — Rolling historical counters (`previous_forgetting_count`, `historical_completion_rate`, etc.) are computed per user in strict chronological order; a row's own label is only added to counters *after* the row is emitted. Assertions in `ml/data/generate_dataset.py` verify this invariant.")
    lines.append("2. **Splitting** — Strict chronological split by global date with overlap assertions in `ml/training/splits.py`. Standard K-fold would leak, so it is replaced with walk-forward time-series CV.")
    lines.append("3. **Calibration & threshold tuning** — Both are fit *only* on the validation split; the test split is touched exactly once for final reporting.")
    lines.append("4. **Preprocessing** — Preprocessor is fit on train (or train-fold) only; fitted medians/scales/one-hot vocabularies are re-used at serve time via the persisted `model_bundle.joblib`.")
    lines.append("")

    lines.append("## Artifact Inventory")
    lines.append("")
    lines.append("- `artifacts/model_bundle.joblib` — Final calibrated model, raw model, fitted preprocessor, threshold, feature lists, SHAP background.")
    lines.append("- `artifacts/feature_metadata.json` — Feature contract (imputer medians, StandardScaler params, one-hot vocab, descriptions).")
    lines.append("- `artifacts/metrics.json` — Machine-readable full metrics (candidates, CV, final).")
    lines.append("- `artifacts/confusion_matrix.png`")
    lines.append("- `artifacts/roc_curve.png` (all candidates overlaid)")
    lines.append("- `artifacts/precision_recall_curve.png` (all candidates)")
    lines.append("- `artifacts/feature_importance.png` (MDI / |coef|)")
    lines.append("- `artifacts/calibration_plot.png`")
    lines.append("- `artifacts/shap_summary_bar.png` (global mean |SHAP|)")
    lines.append("- `artifacts/shap_beeswarm.png` (global SHAP value distribution)")
    lines.append("- `artifacts/shap_individual_waterfalls.png` (LOW/MEDIUM/HIGH individual examples explained)")
    lines.append("- `artifacts/performance_report.md` (this document)")
    lines.append("")

    path = artifacts_dir / "performance_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_report(y_test, final_test_prob, final_test_pred, candidates_prob,
                     y_test_for_candidates, best_model, preprocessor, feature_names,
                     X_test_transformed, best_model_name, artifacts_dir,
                     shap_background=None, raw_model=None,
                     final_metrics=None, all_metrics_dict=None,
                     X_examples=None, example_true_labels=None,
                     example_probabilities=None, example_indices=None,
                     X_train_raw_sample=None):
    artifacts_dir = Path(artifacts_dir)

    plot_confusion_matrix(y_test, final_test_pred, artifacts_dir / "confusion_matrix.png")
    plot_roc_curve(candidates_prob, y_test_for_candidates, artifacts_dir / "roc_curve.png")
    plot_pr_curve(candidates_prob, y_test_for_candidates, artifacts_dir / "precision_recall_curve.png")
    plot_feature_importance(best_model, feature_names, best_model_name, artifacts_dir / "feature_importance.png")
    plot_calibration(y_test, final_test_prob, artifacts_dir / "calibration_plot.png")

    print("  Computing SHAP global plots...")
    plot_shap_global(
        raw_model=raw_model if raw_model is not None else best_model,
        model_name=best_model_name,
        X_shap_background=shap_background,
        X_test_transformed=X_test_transformed,
        feature_names=feature_names,
        artifacts_dir=artifacts_dir,
    )

    print("  Computing SHAP individual examples...")
    if X_examples is not None:
        plot_shap_individual(
            raw_model=raw_model if raw_model is not None else best_model,
            model_name=best_model_name,
            X_shap_background=shap_background,
            X_examples=X_examples,
            example_probabilities=example_probabilities,
            example_true_labels=example_true_labels,
            feature_names=feature_names,
            artifacts_dir=artifacts_dir,
        )

    print("  Writing markdown performance report...")
    if final_metrics is not None and all_metrics_dict is not None:
        write_markdown_report(
            final_metrics=final_metrics,
            all_metrics_dict=all_metrics_dict,
            candidates_prob=candidates_prob,
            y_test=y_test,
            artifacts_dir=artifacts_dir,
        )
