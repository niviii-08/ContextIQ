from app.feedback_store import InMemoryFeedbackStore
from app.schemas import FeedbackEntry, FeedbackType


def test_save_and_retrieve_feedback():
    store = InMemoryFeedbackStore()
    entry = FeedbackEntry(
        user_id="user_123",
        target_type="insight",
        target_id="insight_1",
        feedback=FeedbackType.USEFUL,
    )
    stored_id = store.save(entry)
    assert isinstance(stored_id, str) and stored_id

    entries = store.list_for_user("user_123")
    assert len(entries) == 1
    assert entries[0].feedback == FeedbackType.USEFUL


def test_list_for_user_filters_by_user():
    store = InMemoryFeedbackStore()
    store.save(FeedbackEntry(user_id="a", target_type="insight", target_id="x", feedback=FeedbackType.USEFUL))
    store.save(FeedbackEntry(user_id="b", target_type="insight", target_id="y", feedback=FeedbackType.DISMISSED))

    assert len(store.list_for_user("a")) == 1
    assert len(store.list_for_user("b")) == 1
    assert len(store.list_for_user("c")) == 0
