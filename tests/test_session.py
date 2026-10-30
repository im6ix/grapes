import json

from grapes.agent.session import SessionStore, default_sessions_dir


def test_create_writes_a_header_and_starts_empty(tmp_path):
    store = SessionStore(tmp_path)
    session = store.create()

    assert session.path.exists()
    assert session.path.parent == tmp_path
    assert session.id.startswith("ses_")

    header = json.loads(session.path.read_text().splitlines()[0])
    assert header["type"] == "session"
    assert header["version"] == 1
    assert header["id"] == session.id
    assert session.messages() == []


def test_append_links_entries_and_replays_messages(tmp_path):
    store = SessionStore(tmp_path)
    session = store.create()

    first = session.append("message", {"role": "user", "content": "hi"})
    second = session.append("message", {"role": "assistant", "content": "hello"})

    assert first["id"] == "e1"
    assert first["parent_id"] is None
    assert first["seq"] == 1

    assert second["id"] == "e2"
    assert second["parent_id"] == first["id"]
    assert second["seq"] == 2

    reopened = store.open(session.id)
    assert reopened.messages() == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_list_returns_newest_first(tmp_path, monkeypatch):
    times = iter([1.0, 2.0])
    monkeypatch.setattr("grapes.agent.session.time.time", lambda: next(times))

    store = SessionStore(tmp_path)
    older = store.create()
    newer = store.create()

    assert [header["id"] for header in store.list()] == [newer.id, older.id]


def test_default_sessions_dir_uses_xdg_data_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert default_sessions_dir() == tmp_path / "grapes" / "sessions"
