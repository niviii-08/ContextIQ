"""
'One More Thing' pattern discovery via association-rule mining.

Groups tasks into "baskets" (context sessions, approximated here as
same user + same context_tag + same calendar day) and runs FP-Growth
(via mlxtend) to find task pairs that co-occur frequently — the raw
material for writing rows into the `task_associations` table
(association_type=OFTEN_FORGOTTEN_WITH).

Usage:
    python ml/features/association_mining.py --data-dir data --out data/task_associations.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder


def build_baskets(tasks: pd.DataFrame) -> list[list[str]]:
    tasks = tasks.copy()
    tasks["created_date"] = pd.to_datetime(tasks["created_at"]).dt.date
    baskets = (
        tasks.dropna(subset=["context_tag"])
        .groupby(["user_id", "context_tag", "created_date"])["title"]
        .apply(list)
    )
    return [b for b in baskets.tolist() if len(b) >= 2]


def mine_rules(baskets: list[list[str]], min_support: float = 0.02, min_confidence: float = 0.3) -> pd.DataFrame:
    if not baskets:
        return pd.DataFrame()

    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)

    frequent = fpgrowth(basket_df, min_support=min_support, use_colnames=True)
    if frequent.empty:
        return pd.DataFrame()

    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    # Keep only 1-item -> 1-item rules — cleanest for "task A often precedes/pairs with task B"
    rules = rules[
        (rules["antecedents"].apply(len) == 1) & (rules["consequents"].apply(len) == 1)
    ].copy()
    rules["antecedent"] = rules["antecedents"].apply(lambda s: next(iter(s)))
    rules["consequent"] = rules["consequents"].apply(lambda s: next(iter(s)))

    return rules[["antecedent", "consequent", "support", "confidence", "lift"]].sort_values(
        "lift", ascending=False
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine 'One More Thing' task associations")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--min-support", type=float, default=0.02)
    parser.add_argument("--min-confidence", type=float, default=0.3)
    args = parser.parse_args()

    tasks = pd.read_csv(args.data_dir / "tasks.csv")
    baskets = build_baskets(tasks)
    rules = mine_rules(baskets, args.min_support, args.min_confidence)

    out_path = args.out or (args.data_dir / "task_associations.csv")
    rules.to_csv(out_path, index=False)
    print(f"Found {len(rules)} candidate associations from {len(baskets)} baskets")
    if not rules.empty:
        print(rules.head(10).to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
