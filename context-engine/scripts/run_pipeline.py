"""
End-to-end demonstration pipeline.

Generates synthetic data, runs System A (session reconstruction, metrics,
pattern discovery, recovery cost) and System B (transactions, association
mining, recommendations, combined intelligence), and writes summary
artifacts (CSV + a plot) to artifacts/.

Usage:
    python scripts/run_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datasets.synthetic_data_generator import generate_dataset  # noqa: E402
from ml.context.session_reconstruction import reconstruct_sessions  # noqa: E402
from ml.context.metrics import compute_session_metrics  # noqa: E402
from ml.context.pattern_discovery import discover_all_patterns  # noqa: E402
from ml.context.recovery_cost import estimate_recovery_costs  # noqa: E402
from ml.associations.transactions import generate_transactions, transactions_to_basket_list  # noqa: E402
from ml.associations.mining import mine_association_rules  # noqa: E402
from ml.associations.recommender import (  # noqa: E402
    recommend_for_context,
    prioritize_recommendations,
    MockForgettingRiskProvider,
    RecommendationQualityConfig,
)
from ml.evaluation.evaluate import rule_quality_report, session_summary_report  # noqa: E402

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def main() -> None:
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    print("Generating synthetic dataset...")
    events = generate_dataset(num_users=25, visits_per_user=20, seed=42)
    print(f"  {len(events)} events generated")

    print("\n[System A] Reconstructing sessions...")
    sessions = reconstruct_sessions(events)
    print(f"  {len(sessions)} sessions reconstructed")

    metrics = compute_session_metrics(sessions, scope="synthetic_population")
    print(f"  metrics: {metrics.model_dump()}")

    patterns = discover_all_patterns(sessions)
    print(f"  {len(patterns)} behavioural patterns discovered")

    recovery = estimate_recovery_costs(sessions)
    avg_recovery = sum(r.recovery_cost_score for r in recovery) / len(recovery) if recovery else 0
    print(f"  average recovery cost score: {avg_recovery:.3f}")

    session_df = session_summary_report(sessions)
    session_df.to_csv(ARTIFACTS_DIR / "session_summary.csv", index=False)

    print("\n[System B] Generating transactions...")
    transactions = generate_transactions(events)
    print(f"  {len(transactions)} transactions generated")

    contexts = sorted({t.context for t in transactions})
    all_rules = []
    for context in contexts:
        baskets = transactions_to_basket_list([t for t in transactions if t.context == context])
        rules = mine_association_rules(
            baskets, context=context, algorithm="apriori", min_support=0.1, min_confidence=0.4, min_lift=1.0
        )
        print(f"  [{context}] {len(baskets)} transactions -> {len(rules)} rules")
        all_rules.extend(rules)

    rule_df = rule_quality_report(all_rules)
    rule_df.to_csv(ARTIFACTS_DIR / "association_rules.csv", index=False)

    print("\n[System B] Sample recommendation for context 'department'...")
    dept_rules = [r for r in all_rules if r.context == "department"]
    recs = recommend_for_context(
        user_id="user_000",
        context="department",
        rules=dept_rules,
        completed_tasks=[],
        config=RecommendationQualityConfig(min_confidence=0.3, min_support=0.05, min_lift=1.0),
    )
    for r in recs:
        print(f"  -> {r.task} (confidence={r.confidence}, support={r.support}, lift={r.lift})")

    print("\n[Combined Intelligence] Prioritizing with mock forgetting-risk provider...")
    mock_provider = MockForgettingRiskProvider()
    prioritized = prioritize_recommendations("user_000", recs, forgetting_provider=mock_provider)
    for p in prioritized:
        print(
            f"  -> {p.task} (assoc_conf={p.association_confidence}, "
            f"forgetting_prob={p.forgetting_probability}, priority={p.priority_score})"
        )

    # Simple plot: distribution of session focused vs interruption time.
    if not session_df.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(session_df["focused_s"], session_df["interruption_s"], alpha=0.5)
        ax.set_xlabel("Focused time (s)")
        ax.set_ylabel("Interruption time (s)")
        ax.set_title("Focused vs interruption time per session")
        fig.tight_layout()
        fig.savefig(ARTIFACTS_DIR / "focused_vs_interruption.png", dpi=150)
        plt.close(fig)

    print(f"\nArtifacts written to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
