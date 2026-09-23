from datetime import datetime, timedelta

from app.schemas.events import RawEvent, EventType
from ml.associations.transactions import generate_transactions, transactions_to_basket_list


def _complete_event(user_id, task_id, context, offset_seconds):
    return RawEvent(
        user_id=user_id,
        timestamp=datetime(2026, 1, 1, 9, 0, 0) + timedelta(seconds=offset_seconds),
        task_id=task_id,
        task_category="admin",
        context=context,
        event_type=EventType.COMPLETE,
    )


def test_single_visit_becomes_one_transaction():
    events = [
        _complete_event("u1", "collect_form", "department", 0),
        _complete_event("u1", "submit_record", "department", 60),
        _complete_event("u1", "ask_faculty", "department", 120),
    ]
    txns = generate_transactions(events, session_gap_minutes=60)
    assert len(txns) == 1
    assert set(txns[0].tasks) == {"collect_form", "submit_record", "ask_faculty"}


def test_large_gap_creates_two_transactions():
    events = [
        _complete_event("u1", "collect_form", "department", 0),
        _complete_event("u1", "submit_record", "department", 7200),  # 2 hours later
    ]
    txns = generate_transactions(events, session_gap_minutes=60)
    assert len(txns) == 2


def test_non_complete_events_ignored():
    events = [
        RawEvent(
            user_id="u1",
            timestamp=datetime(2026, 1, 1, 9, 0, 0),
            task_id="t1",
            task_category="admin",
            context="department",
            event_type=EventType.START,
        )
    ]
    txns = generate_transactions(events)
    assert txns == []


def test_different_contexts_produce_separate_transactions():
    events = [
        _complete_event("u1", "collect_form", "department", 0),
        _complete_event("u1", "borrow_book", "library", 30),
    ]
    txns = generate_transactions(events, session_gap_minutes=60)
    assert len(txns) == 2
    contexts = {t.context for t in txns}
    assert contexts == {"department", "library"}


def test_transactions_to_basket_list():
    events = [
        _complete_event("u1", "collect_form", "department", 0),
        _complete_event("u1", "submit_record", "department", 60),
    ]
    txns = generate_transactions(events)
    baskets = transactions_to_basket_list(txns)
    assert baskets == [["collect_form", "submit_record"]]
