"""
Generate a synthetic event dataset and save it as JSON under datasets/.

Usage:
    python scripts/generate_synthetic_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datasets.synthetic_data_generator import generate_dataset  # noqa: E402


def main() -> None:
    events = generate_dataset(num_users=25, visits_per_user=20, seed=42)
    out_path = Path(__file__).resolve().parents[1] / "datasets" / "synthetic_events.json"
    payload = [
        {
            "user_id": e.user_id,
            "timestamp": e.timestamp.isoformat(),
            "task_id": e.task_id,
            "task_category": e.task_category,
            "context": e.context,
            "event_type": e.event_type,
            "interruption_source": e.interruption_source,
        }
        for e in events
    ]
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(payload)} events to {out_path}")


if __name__ == "__main__":
    main()
