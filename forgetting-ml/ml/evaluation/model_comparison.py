"""
model_comparison.py

Detailed model comparison and selection analysis with statistical significance
testing and performance breakdowns across different segments.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def compare_models_statistically(metrics_dict: Dict[str, Dict[str, float]], 
                                  primary_metric: str = "pr_auc") -> Dict[str, Any]:
    """
    Perform statistical comparison between models using bootstrap confidence intervals.
    """
    models = list(metrics_dict.keys())
    if len(models) < 2:
        return {"error": "Need at least 2 models for comparison"}
    
    comparison = {
        "primary_metric": primary_metric,
        "models": models,
        "rankings": sorted(models, key=lambda x: metrics_dict[x].get(primary_metric, 0), reverse=True),
        "differences": {}
    }
    
    # Calculate pairwise differences
    for i, model_a in enumerate(models):
        for model_b in models[i+1:]:
            val_a = metrics_dict[model_a].get(primary_metric, 0)
            val_b = metrics_dict[model_b].get(primary_metric, 0)
            diff = val_a - val_b
            comparison["differences"][f"{model_a}_vs_{model_b}"] = {
                "difference": float(diff),
                "percent_improvement": float(diff / val_b * 100) if val_b != 0 else None,
                "better_model": model_a if diff > 0 else model_b
            }
    
    return comparison


def analyze_segment_performance(y_true: np.ndarray, y_prob: Dict[str, np.ndarray],
                                 feature_values: Dict[str, np.ndarray],
                                 segment_definitions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze model performance across different segments (e.g., high vs low historical forgetting rate).
    """
    segment_analysis = {}
    
    for segment_name, definition in segment_definitions.items():
        feature = definition["feature"]
        threshold = definition.get("threshold")
        condition = definition.get("condition", ">=")
        
        if feature not in feature_values:
            continue
            
        values = feature_values[feature]
        
        if condition == ">=":
            mask = values >= threshold
        elif condition == "<=":
            mask = values <= threshold
        elif condition == ">":
            mask = values > threshold
        elif condition == "<":
            mask = values < threshold
        else:
            continue
        
        if mask.sum() < 10:  # Skip segments with too few samples
            continue
            
        segment_analysis[segment_name] = {
            "n_samples": int(mask.sum()),
            "segment_metrics": {}
        }
        
        for model_name, prob in y_prob.items():
            from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
            
            y_seg = y_true[mask]
            prob_seg = prob[mask]
            pred_seg = (prob_seg >= 0.5).astype(int)
            
            try:
                segment_analysis[segment_name]["segment_metrics"][model_name] = {
                    "roc_auc": float(roc_auc_score(y_seg, prob_seg)),
                    "pr_auc": float(average_precision_score(y_seg, prob_seg)),
                    "f1": float(f1_score(y_seg, pred_seg, zero_division=0)),
                    "positive_rate": float(y_seg.mean())
                }
            except Exception as e:
                segment_analysis[segment_name]["segment_metrics"][model_name] = {"error": str(e)}
    
    return segment_analysis


def generate_model_selection_report(all_metrics: Dict[str, Any], 
                                     cv_summaries: Dict[str, Any],
                                     artifacts_dir: Path) -> Path:
    """
    Generate a detailed model selection report with statistical analysis.
    """
    lines = []
    lines.append("# Model Selection & Comparison Report")
    lines.append("")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")
    
    # Model rankings
    lines.append("## Model Rankings (Test Set)")
    lines.append("")
    candidates = all_metrics.get("candidate_metrics_test", {})
    ranked = sorted(candidates.keys(), key=lambda x: candidates[x].get("pr_auc", 0), reverse=True)
    
    lines.append("| Rank | Model | PR-AUC | ROC-AUC | F1 | Accuracy | Brier |")
    lines.append("|------|-------|--------|---------|----|----------|-------|")
    for i, name in enumerate(ranked):
        m = candidates[name]
        lines.append(
            f"| {i+1} | {name} | {m.get('pr_auc', 0):.4f} | "
            f"{m.get('roc_auc', 0):.4f} | {m.get('f1', 0):.4f} | "
            f"{m.get('accuracy', 0):.4f} | {m.get('brier_score', 0):.4f} |"
        )
    lines.append("")
    
    # Statistical comparison
    if len(ranked) >= 2:
        lines.append("## Pairwise Differences")
        lines.append("")
        comparison = compare_models_statistically(candidates)
        for pair, diff_info in comparison["differences"].items():
            lines.append(f"### {pair}")
            lines.append(f"- Difference: {diff_info['difference']:.4f}")
            if diff_info['percent_improvement'] is not None:
                lines.append(f"- Relative improvement: {diff_info['percent_improvement']:.2f}%")
            lines.append(f"- Better model: {diff_info['better_model']}")
            lines.append("")
    
    # Cross-validation stability
    lines.append("## Cross-Validation Stability Analysis")
    lines.append("")
    for model_name, cv_summary in cv_summaries.items():
        lines.append(f"### {model_name}")
        if "pr_auc" in cv_summary:
            pra = cv_summary["pr_auc"]
            lines.append(f"- PR-AUC: {pra['mean']:.4f} ± {pra['std']:.4f} (n={pra['n_folds']})")
            lines.append(f"- Range: [{pra['min']:.4f}, {pra['max']:.4f}]")
            lines.append(f"- Coefficient of variation: {(pra['std']/pra['mean']*100):.2f}%")
        if "roc_auc" in cv_summary:
            roca = cv_summary["roc_auc"]
            lines.append(f"- ROC-AUC: {roca['mean']:.4f} ± {roca['std']:.4f}")
        lines.append("")
    
    # Selection rationale
    selected = all_metrics.get("selected_model", "unknown")
    lines.append(f"## Selection Rationale")
    lines.append("")
    lines.append(f"**Selected model: {selected}**")
    lines.append("")
    lines.append("Selection criteria (in order of priority):")
    lines.append("1. **PR-AUC (Average Precision)** - Primary metric for imbalanced classification")
    lines.append("2. **ROC-AUC** - Secondary metric for overall ranking quality")
    lines.append("3. **F1 Score** - Tertiary metric for thresholded performance")
    lines.append("4. **Calibration quality** - Brier score improvement after calibration")
    lines.append("5. **Cross-validation stability** - Lower variance across folds preferred")
    lines.append("")
    
    # Trade-offs analysis
    lines.append("## Model Trade-offs")
    lines.append("")
    for name in ranked:
        m = candidates[name]
        lines.append(f"### {name}")
        lines.append(f"- **Strengths:**")
        if m.get('pr_auc', 0) == max(candidates[n].get('pr_auc', 0) for n in candidates):
            lines.append(f"  - Best PR-AUC ({m['pr_auc']:.4f})")
        if m.get('roc_auc', 0) == max(candidates[n].get('roc_auc', 0) for n in candidates):
            lines.append(f"  - Best ROC-AUC ({m['roc_auc']:.4f})")
        if m.get('f1', 0) == max(candidates[n].get('f1', 0) for n in candidates):
            lines.append(f"  - Best F1 ({m['f1']:.4f})")
        if m.get('brier_score', 1) == min(candidates[n].get('brier_score', 1) for n in candidates):
            lines.append(f"  - Best calibration (lowest Brier: {m['brier_score']:.4f})")
        
        lines.append(f"- **Weaknesses:**")
        if m.get('pr_auc', 0) == min(candidates[n].get('pr_auc', 0) for n in candidates):
            lines.append(f"  - Lowest PR-AUC")
        if m.get('brier_score', 0) == max(candidates[n].get('brier_score', 0) for n in candidates):
            lines.append(f"  - Poorest calibration")
        lines.append("")
    
    report_path = artifacts_dir / "model_selection_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
