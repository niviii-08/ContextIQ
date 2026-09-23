"""
Tests for reproducible dataset generation, leakage-proof feature construction,
and dataset metadata output.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys_path_added = False
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))
    sys_path_added = True

from ml.data.generate_dataset import (
    sample_user_archetypes,
    generate_events,
    _assert_no_target_leakage,
    _fingerprint_df,
)
from ml.training.config import SEED, DATASET_CONFIG


def test_user_archetypes_reproducible():
    u1 = sample_user_archetypes(50)
    u2 = sample_user_archetypes(50)
    assert len(u1) == 50
    assert u1["forgetfulness_trait"].equals(u2["forgetfulness_trait"])
    assert "user_id" in u1.columns
    assert u1["user_id"].is_unique


def test_generate_events_sorted_chronologically():
    users = sample_user_archetypes(8)
    events = generate_events(users)
    assert len(events) >= 1
    # Dataset is globally sorted
    event_tuples = list(zip(events["date"], events["user_id"], events["hour"]))
    assert event_tuples == sorted(event_tuples)


def test_generate_events_target_column():
    users = sample_user_archetypes(5)
    events = generate_events(users)
    assert "forgotten" in events.columns
    vals = set(events["forgotten"].unique())
    assert vals <= {0, 1}
    # Should contain a mix of both classes with high probability for 10k+ rows
    assert len(events) >= 100


def test_leakage_assertion_passes_on_generated_data():
    users = sample_user_archetypes(5)
    events = generate_events(users)
    sample = events[events["user_id"].isin(events["user_id"].unique()[:3])]
    _assert_no_target_leakage(sample)


def test_leakage_assertion_detects_bad_rate():
    users = sample_user_archetypes(2)
    events = generate_events(users)
    # Take one user and manually corrupt row 2's historical_forgetting_rate
    bad = events.copy().reset_index(drop=True)
    uid = bad["user_id"].iloc[0]
    user_idx = bad.index[bad["user_id"] == uid].tolist()
    if len(user_idx) < 3:
        pytest.skip("Not enough rows for single user in small sample")
    target = user_idx[2]
    bad.at[target, "historical_forgetting_rate"] = 1.0
    # Also force previous_forgetting_count to wrong value for determinism
    bad.at[target, "previous_forgetting_count"] = 99999
    with pytest.raises(AssertionError):
        _assert_no_target_leakage(bad[bad["user_id"] == uid])


def test_fingerprint_deterministic():
    users = sample_user_archetypes(5)
    events = generate_events(users)
    f1 = _fingerprint_df(events)
    f2 = _fingerprint_df(events)
    assert f1 == f2
    assert isinstance(f1, str)
    assert len(f1) == 16


def test_fingerprint_changes_when_rows_change():
    users = sample_user_archetypes(5)
    events = generate_events(users)
    f1 = _fingerprint_df(events)
    events2 = events.copy()
    events2.iloc[0, events2.columns.get_loc("forgotten")] = int(
        not bool(events2.iloc[0]["forgotten"])
    )
    f2 = _fingerprint_df(events2)
    assert f1 != f2


def test_dataset_main_writes_files(tmp_path, monkeypatch):
    import ml.data.generate_dataset as gen_mod

    monkeypatch.setattr(gen_mod, "OUT_DIR", tmp_path)
    gen_mod.main()

    tasks_csv = tmp_path / "tasks_raw.csv"
    users_csv = tmp_path / "users.csv"
    meta_json = tmp_path / "dataset_metadata.json"

    assert tasks_csv.exists()
    assert users_csv.exists()
    assert meta_json.exists()

    df = pd.read_csv(tasks_csv)
    assert len(df) >= DATASET_CONFIG["min_observations"]

    with open(meta_json) as f:
        meta = json.load(f)
    assert meta["seed"] == SEED
    assert "fingerprint_sha256_16" in meta
    assert meta["leakage_check_status"] == "passed"
    assert "feature_columns" in meta
    assert meta["feature_columns"]["target"] == "forgotten"
    assert len(meta["feature_columns"]["numeric"]) >= 10
    assert len(meta["feature_columns"]["categorical"]) == 3


def test_historical_features_monotonic_in_user_history():
    """previous_completion_count is non-decreasing within each user history."""
    users = sample_user_archetypes(5)
    events = generate_events(users)
    for uid, g in events.groupby("user_id"):
        g = g.sort_values(["date", "hour"]).reset_index(drop=True)
        pcc = g["previous_completion_count"].tolist()
        pfc = g["previous_forgetting_count"].tolist()
        for i in range(1, len(pcc)):
            assert pcc[i] >= pcc[i - 1], f"pcc dropped at row {i} user {uid}"
            assert pfc[i] >= pfc[i - 1], f"pfc dropped at row {i} user {uid}"
