"""
examples/run_example.py
========================
Demonstrates using the module end-to-end with a fixture JSON file, without
starting the FastAPI server and without any external ContextIQ dependency.

Run:
    python examples/run_example.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.daily_summary import generate_daily_summary
from app.insight_engine import generate_insights
from app.llm.explanation_service import generate_explanation
from app.llm.provider import MockLLMProvider
from app.ranking import rank_insights
from app.recommendations import generate_recommendations
from app.schemas import IntelligenceBundle, LLMExplanationRequest


def main():
    fixture_path = os.path.join(os.path.dirname(__file__), "sample_bundle.json")
    with open(fixture_path) as f:
        raw = json.load(f)

    bundle = IntelligenceBundle.model_validate(raw)

    print("=== Insights ===")
    insights = generate_insights(bundle)
    ranked = rank_insights(insights)
    provider = MockLLMProvider()
    for ins in ranked:
        req = LLMExplanationRequest(
            type=ins.type.value,
            payload={"title": ins.title, "description": ins.description},
        )
        result = generate_explanation(req, provider)
        print(f"[{ins.priority.value}] {ins.title} (score={ins.rank_score})")
        print(f"  -> {result.text}")

    print("\n=== Daily Summary ===")
    summary = generate_daily_summary(bundle)
    print(summary.model_dump_json(indent=2))

    print("\n=== Recommendations ===")
    recs = generate_recommendations(bundle)
    for r in recs:
        print(f"[{r.priority.value}] {r.headline}: {r.explanation}")


if __name__ == "__main__":
    main()
