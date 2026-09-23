"""
calibration_analysis.py

Detailed probability calibration analysis with reliability diagrams,
expected calibration error (ECE), and calibration curve analysis.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _save(fig, path, dpi=150):
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, 
                                       n_bins: int = 10) -> Dict[str, Any]:
    """
    Compute Expected Calibration Error (ECE) - a weighted average of calibration
    error across bins, weighted by the number of samples in each bin.
    """
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    
    # Compute weights (number of samples in each bin)
    bin_edges = np.percentile(y_prob, np.linspace(0, 100, n_bins + 1))
    bin_indices = np.digitize(y_prob, bin_edges) - 1
    bin_counts = np.bincount(bin_indices, minlength=n_bins)
    
    # Compute ECE
    ece = 0.0
    total_samples = len(y_true)
    
    for i in range(n_bins):
        if bin_counts[i] > 0:
            weight = bin_counts[i] / total_samples
            calibration_error = abs(frac_pos[i] - mean_pred[i])
            ece += weight * calibration_error
    
    return {
        "ece": float(ece),
        "n_bins": n_bins,
        "bin_fractions_positive": [float(x) for x in frac_pos],
        "bin_mean_predictions": [float(x) for x in mean_pred],
        "bin_counts": [int(x) for x in bin_counts],
    }


def plot_detailed_calibration(y_true: np.ndarray, y_prob: np.ndarray, 
                               model_name: str, out_path: Path):
    """
    Create a detailed calibration plot with reliability diagram, histogram,
    and reference lines.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Reliability diagram
    n_bins = 10
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    
    ax1.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly calibrated")
    ax1.plot(mean_pred, frac_pos, marker="o", linewidth=2, label=model_name, color="#4C78A8")
    ax1.fill_between(mean_pred, 0, frac_pos, alpha=0.2, color="#4C78A8")
    ax1.fill_between(mean_pred, frac_pos, 1, alpha=0.1, color="#E45756")
    
    ax1.set_xlabel("Mean predicted probability")
    ax1.set_ylabel("Fraction of positives")
    ax1.set_title(f"Reliability Diagram - {model_name}")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 1])
    ax1.set_ylim([0, 1])
    
    # Histogram of predicted probabilities
    ax2.hist(y_prob, bins=20, edgecolor="black", alpha=0.7, color="#4C78A8")
    ax2.axvline(y_prob.mean(), color="red", linestyle="--", 
                label=f"Mean: {y_prob.mean():.3f}")
    ax2.set_xlabel("Predicted probability")
    ax2.set_ylabel("Count")
    ax2.set_title("Distribution of Predicted Probabilities")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    _save(fig, out_path)


def compare_calibration_methods(y_true: np.ndarray, 
                                  probabilities: Dict[str, np.ndarray],
                                  out_path: Path):
    """
    Compare calibration quality across multiple models/calibration methods.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    for name, prob in probabilities.items():
        frac_pos, mean_pred = calibration_curve(y_true, prob, n_bins=10, strategy="quantile")
        ax.plot(mean_pred, frac_pos, marker="o", label=name, linewidth=2)
    
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly calibrated")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Calibration Comparison Across Models")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    _save(fig, out_path)


def generate_calibration_report(y_true: np.ndarray, 
                                 model_probabilities: Dict[str, np.ndarray],
                                 artifacts_dir: Path) -> Path:
    """
    Generate a comprehensive calibration analysis report.
    """
    lines = []
    lines.append("# Probability Calibration Analysis Report")
    lines.append("")
    lines.append("This report analyzes the calibration quality of trained models.")
    lines.append("Well-calibrated probabilities are important when the model's")
    lines.append("predicted probabilities will be used for decision-making.")
    lines.append("")
    
    # Compute metrics for each model
    calibration_metrics = {}
    for model_name, prob in model_probabilities.items():
        brier = brier_score_loss(y_true, prob)
        ece_info = compute_expected_calibration_error(y_true, prob)
        calibration_metrics[model_name] = {
            "brier_score": float(brier),
            "expected_calibration_error": ece_info["ece"],
            "n_bins": ece_info["n_bins"],
        }
    
    # Summary table
    lines.append("## Calibration Metrics Summary")
    lines.append("")
    lines.append("| Model | Brier Score | ECE | Interpretation |")
    lines.append("|-------|-------------|-----|----------------|")
    
    for name, metrics in calibration_metrics.items():
        brier = metrics["brier_score"]
        ece = metrics["expected_calibration_error"]
        
        # Interpretation
        if ece < 0.05:
            interp = "Excellent"
        elif ece < 0.10:
            interp = "Good"
        elif ece < 0.15:
            interp = "Fair"
        else:
            interp = "Poor"
        
        lines.append(f"| {name} | {brier:.4f} | {ece:.4f} | {interp} |")
    lines.append("")
    
    # Detailed explanation
    lines.append("## Metric Definitions")
    lines.append("")
    lines.append("### Brier Score")
    lines.append("- Measures the mean squared difference between predicted probabilities")
    lines.append("  and actual outcomes.")
    lines.append("- Lower is better (0 = perfect, 0.25 = random for binary classification).")
    lines.append("- Combines both calibration and refinement (discrimination).")
    lines.append("")
    
    lines.append("### Expected Calibration Error (ECE)")
    lines.append("- Weighted average of calibration error across probability bins.")
    lines.append("- Lower is better (0 = perfectly calibrated).")
    lines.append("- Focuses specifically on calibration quality, independent of discrimination.")
    lines.append("")
    
    lines.append("## Interpretation for Forgetting-Risk Prediction")
    lines.append("")
    lines.append("For forgetting-risk prediction, calibration matters because:")
    lines.append("- Users may interpret a 70% risk as 'highly likely to forget'")
    lines.append("- If the model is poorly calibrated, a 70% prediction might actually")
    lines.append("  correspond to a 40% or 90% true risk")
    lines.append("- Good calibration enables trustworthy probability-based decision making")
    lines.append("- Threshold selection (e.g., 'flag tasks above 50% risk') depends on")
    lines.append("  accurate probability estimates")
    lines.append("")
    
    # Per-bin analysis for the best model
    best_model = min(calibration_metrics.keys(), 
                     key=lambda x: calibration_metrics[x]["expected_calibration_error"])
    
    lines.append(f"## Detailed Bin Analysis - {best_model}")
    lines.append("")
    lines.append("| Bin | Mean Predicted | Fraction Positive | Sample Count | Calibration Error |")
    lines.append("|-----|----------------|-------------------|--------------|-------------------|")
    
    ece_info = compute_expected_calibration_error(y_true, model_probabilities[best_model])
    n_bins = min(len(ece_info["bin_mean_predictions"]), 
                 len(ece_info["bin_fractions_positive"]), 
                 len(ece_info["bin_counts"]))
    for i in range(n_bins):
        mean_pred = ece_info["bin_mean_predictions"][i]
        frac_pos = ece_info["bin_fractions_positive"][i]
        count = ece_info["bin_counts"][i]
        cal_error = abs(frac_pos - mean_pred)
        lines.append(f"| {i+1} | {mean_pred:.3f} | {frac_pos:.3f} | {count} | {cal_error:.3f} |")
    lines.append("")
    
    # Save metrics
    metrics_path = artifacts_dir / "calibration_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(calibration_metrics, f, indent=2, default=str)
    
    # Save report
    report_path = artifacts_dir / "calibration_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    
    return report_path
