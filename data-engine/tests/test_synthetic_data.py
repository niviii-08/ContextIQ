from scripts.generate_synthetic_data import SyntheticDataGenerator, PERSONAS


def test_generator_produces_expected_row_counts():
    gen = SyntheticDataGenerator(num_users=5, num_days=7, seed=1)
    frames = gen.generate()

    assert len(frames["users"]) == 5
    assert len(frames["tasks"]) > 0
    assert len(frames["task_events"]) > 0
    # every task should have at least a "created" event
    assert len(frames["task_events"]) >= len(frames["tasks"])


def test_generator_is_reproducible_with_same_seed():
    gen1 = SyntheticDataGenerator(num_users=3, num_days=5, seed=99)
    gen2 = SyntheticDataGenerator(num_users=3, num_days=5, seed=99)

    frames1 = gen1.generate()
    frames2 = gen2.generate()

    assert len(frames1["tasks"]) == len(frames2["tasks"])
    assert len(frames1["task_events"]) == len(frames2["task_events"])
    assert list(frames1["tasks"]["category"]) == list(frames2["tasks"]["category"])


def test_generator_different_seeds_differ():
    gen1 = SyntheticDataGenerator(num_users=3, num_days=5, seed=1)
    gen2 = SyntheticDataGenerator(num_users=3, num_days=5, seed=2)

    frames1 = gen1.generate()
    frames2 = gen2.generate()

    # extremely unlikely to be identical across different seeds
    assert len(frames1["task_events"]) != len(frames2["task_events"]) or list(
        frames1["tasks"]["category"]
    ) != list(frames2["tasks"]["category"])


def test_every_task_has_a_valid_terminal_or_active_status():
    gen = SyntheticDataGenerator(num_users=5, num_days=10, seed=7)
    frames = gen.generate()
    valid_statuses = {"created", "started", "paused", "resumed", "completed", "forgotten", "cancelled"}
    assert set(frames["tasks"]["status"].unique()).issubset(valid_statuses)


def test_personas_are_behaviourally_distinct():
    names = {p.name for p in PERSONAS}
    assert names == {
        "frequent_forgetter",
        "frequent_interrupter",
        "location_dependent_forgetter",
        "high_focus_user",
        "high_context_switch_user",
    }
    # sanity: the "forgetter" persona should have a meaningfully higher
    # forgetting probability than the "high focus" persona
    forgetter = next(p for p in PERSONAS if p.name == "frequent_forgetter")
    focused = next(p for p in PERSONAS if p.name == "high_focus_user")
    assert forgetter.forgetting_prob > focused.forgetting_prob


def test_zero_users_produces_empty_frames():
    gen = SyntheticDataGenerator(num_users=0, num_days=5, seed=1)
    frames = gen.generate()
    assert len(frames["users"]) == 0
    assert len(frames["tasks"]) == 0
