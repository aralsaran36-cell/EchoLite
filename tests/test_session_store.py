from app.core.session_store import SessionStore


def test_create_session():
    store = SessionStore()

    session = store.get_or_create("s1")

    assert session.session_id == "s1"
    assert session.history == []


def test_add_turn():
    store = SessionStore()

    store.add_turn(
        "s1",
        "Hello",
        "Hi",
    )

    history = store.get_history("s1")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi"


def test_history_limit():
    store = SessionStore(max_history_turns=2)

    for i in range(5):
        store.add_turn(
            "s1",
            f"user {i}",
            f"assistant {i}",
        )

    history = store.get_history("s1")

    assert len(history) == 4


def test_clear_session():
    store = SessionStore()

    store.add_turn("s1", "Hello", "Hi")
    store.clear("s1")

    session = store.get_or_create("s1")

    assert session.history == []


def test_multiple_sessions_are_separate():
    store = SessionStore()

    store.add_turn("s1", "Hello", "Hi")
    store.add_turn("s2", "Vanakkam", "Vanakkam")

    history1 = store.get_history("s1")
    history2 = store.get_history("s2")

    assert history1[0]["content"] == "Hello"
    assert history2[0]["content"] == "Vanakkam"