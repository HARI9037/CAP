"""Phase 3 – User isolation tests.

Verifies that:
- User A can access their own sessions, memories, and settings.
- User B CANNOT access User A's sessions, memories, or settings.
- Unauthenticated requests return 401 on all protected endpoints.

Uses dependency_overrides to inject deterministic user IDs without
requiring a real Clerk JWT, matching the pattern in test_auth_enforcement.py.
"""

import pytest
from fastapi.testclient import TestClient

from main import create_app
from app.memory.store import memory_store
from app.utils.auth import get_current_user_id
from app.utils.env import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

USER_A = "test-user-a"
USER_B = "test-user-b"


@pytest.fixture()
def test_settings(tmp_path):
    """Isolated DB per test so users never share persisted state."""
    return Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=tmp_path / "isolation.db",
        cors_origins=["http://localhost:5173"],
    )


@pytest.fixture(autouse=True)
def _init_memory_store(test_settings):
    """Point the shared memory_store singleton at the isolated test DB."""
    create_app(settings=test_settings)
    yield


def _authenticated_client(test_settings, user_id: str) -> TestClient:
    """Each user gets its own FastAPI app so dependency overrides do not clash."""
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_current_user_id] = lambda uid=user_id: uid
    return TestClient(app)


@pytest.fixture()
def client_a(test_settings):
    """TestClient authenticated as User A."""
    client = _authenticated_client(test_settings, USER_A)
    yield client
    client.app.dependency_overrides.clear()


@pytest.fixture()
def client_b(test_settings):
    """TestClient authenticated as User B."""
    client = _authenticated_client(test_settings, USER_B)
    yield client
    client.app.dependency_overrides.clear()


@pytest.fixture()
def client_anon(test_settings):
    """TestClient with NO authentication (no dependency override)."""
    app = create_app(settings=test_settings)
    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# 1. User A can access own session
# ---------------------------------------------------------------------------

def test_user_a_can_list_own_sessions(client_a):
    """User A creates a session via the store and can list it."""
    session_id = memory_store.create_session(user_id=USER_A)
    resp = client_a.get("/history")
    assert resp.status_code == 200
    session_ids = [s["session_id"] for s in resp.json()["conversations"]]
    assert session_id in session_ids


def test_user_a_can_read_own_session_messages(client_a):
    """User A can retrieve messages from their own session."""
    session_id = memory_store.create_session(user_id=USER_A)
    memory_store.append_message(session_id, "user", "hello", user_id=USER_A)
    resp = client_a.get(f"/history/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["session_id"] == session_id
    assert len(resp.json()["messages"]) >= 1


# ---------------------------------------------------------------------------
# 2. User A can access own memory
# ---------------------------------------------------------------------------

def test_user_a_can_create_and_list_memory(client_a):
    """User A creates a memory item and can list it."""
    payload = {
        "memory_type": "preference",
        "title": "Dark mode",
        "content": "User prefers dark mode",
    }
    resp = client_a.post("/memory/items", json=payload)
    assert resp.status_code == 200
    mem_id = resp.json()["memory"]["memory_id"]

    resp = client_a.get("/memory/items")
    assert resp.status_code == 200
    ids = [m["memory_id"] for m in resp.json()["memories"]]
    assert mem_id in ids


# ---------------------------------------------------------------------------
# 3. User A can access own settings
# ---------------------------------------------------------------------------

def test_user_a_can_read_and_update_settings(client_a):
    """User A can read and update their own settings."""
    resp = client_a.get("/settings")
    assert resp.status_code == 200
    assert "theme" in resp.json()["settings"]

    resp = client_a.put("/settings", json={"theme": "light"})
    assert resp.status_code == 200
    assert resp.json()["settings"]["theme"] == "light"

    # Confirm persistence
    resp = client_a.get("/settings")
    assert resp.json()["settings"]["theme"] == "light"


# ---------------------------------------------------------------------------
# 4. User B CANNOT access User A's session
# ---------------------------------------------------------------------------

def test_user_b_cannot_list_user_a_sessions(client_a, client_b):
    """User B's session list must NOT contain User A's sessions."""
    session_id = memory_store.create_session(user_id=USER_A)

    resp = client_b.get("/history")
    assert resp.status_code == 200
    session_ids = [s["session_id"] for s in resp.json()["conversations"]]
    assert session_id not in session_ids


def test_user_b_cannot_read_user_a_session_messages(client_a, client_b):
    """User B retrieving User A's session returns empty messages (no data leak)."""
    session_id = memory_store.create_session(user_id=USER_A)
    memory_store.append_message(session_id, "user", "secret message", user_id=USER_A)

    resp = client_b.get(f"/history/{session_id}")
    assert resp.status_code == 200
    # The JOIN filters by user_id, so User B gets zero messages
    assert len(resp.json()["messages"]) == 0


def test_user_b_cannot_delete_user_a_session(client_a, client_b):
    """User B cannot delete User A's session."""
    session_id = memory_store.create_session(user_id=USER_A)
    memory_store.append_message(session_id, "user", "keep this", user_id=USER_A)

    client_b.delete(f"/history/{session_id}")

    # Verify the session still exists for User A
    resp = client_a.get(f"/history/{session_id}")
    assert resp.status_code == 200
    assert len(resp.json()["messages"]) >= 1


# ---------------------------------------------------------------------------
# 5. User B CANNOT access User A's memory
# ---------------------------------------------------------------------------

def test_user_b_cannot_list_user_a_memories(client_a, client_b):
    """User B's memory list must NOT contain User A's memories."""
    payload = {
        "memory_type": "preference",
        "title": "A's secret",
        "content": "classified",
    }
    client_a.post("/memory/items", json=payload)

    resp = client_b.get("/memory/items")
    assert resp.status_code == 200
    titles = [m["title"] for m in resp.json()["memories"]]
    assert "A's secret" not in titles


def test_user_b_cannot_delete_user_a_memory(client_a, client_b):
    """User B cannot delete User A's memory – returns 404."""
    payload = {
        "memory_type": "context",
        "title": "Protected",
        "content": "do not delete",
    }
    resp = client_a.post("/memory/items", json=payload)
    mem_id = resp.json()["memory"]["memory_id"]

    resp = client_b.delete(f"/memory/items/{mem_id}")
    assert resp.status_code == 404  # delete_memory returns False → 404

    # Confirm it still exists for User A
    resp = client_a.get("/memory/items")
    ids = [m["memory_id"] for m in resp.json()["memories"]]
    assert mem_id in ids


# ---------------------------------------------------------------------------
# 6. User B CANNOT access User A's settings
# ---------------------------------------------------------------------------

def test_user_b_settings_independent_of_user_a(client_a, client_b):
    """User B's settings are independent of User A's settings."""
    # User A sets theme to light
    client_a.put("/settings", json={"theme": "light"})

    # User B's settings should still be the default (dark)
    resp = client_b.get("/settings")
    assert resp.status_code == 200
    assert resp.json()["settings"]["theme"] == "dark"


# ---------------------------------------------------------------------------
# 7. Unauthenticated requests return 401
# ---------------------------------------------------------------------------

def test_unauth_chat(client_anon):
    resp = client_anon.post("/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_unauth_history(client_anon):
    resp = client_anon.get("/history")
    assert resp.status_code == 401


def test_unauth_memory_list(client_anon):
    resp = client_anon.get("/memory/items")
    assert resp.status_code == 401


def test_unauth_memory_create(client_anon):
    resp = client_anon.post("/memory/items", json={
        "memory_type": "preference", "title": "x", "content": "y"
    })
    assert resp.status_code == 401


def test_unauth_settings_get(client_anon):
    resp = client_anon.get("/settings")
    assert resp.status_code == 401


def test_unauth_settings_put(client_anon):
    resp = client_anon.put("/settings", json={"theme": "dark"})
    assert resp.status_code == 401


def test_unauth_feedback(client_anon):
    resp = client_anon.post("/feedback", json={"rating": 5})
    assert resp.status_code == 401
