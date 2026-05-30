from fastapi.testclient import TestClient

from app.memory.store import memory_store
from app.utils.env import Settings
from main import create_app


def _settings(db_path):
    return Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
        groq_api_key="test-key",
    )


def test_confirm_approve_executes_once_and_returns_memory_summary(tmp_path):
    app = create_app(settings=_settings(tmp_path / "confirm.db"))
    action = {
        "action_id": "save-1",
        "action_type": "save",
        "description": "Save a release note.",
        "payload": {
            "title": "Release Note",
            "content": "The trust workflow is production-ready.",
        },
    }

    with TestClient(app) as client:
        memory_store.ensure_session("confirm-session")
        memory_store.store_pending_actions("confirm-session", [action])

        first = client.post(
            "/confirm",
            json={
                "action_id": "save-1",
                "action_type": "save",
                "approved": True,
                "session_id": "confirm-session",
            },
        ).json()
        second = client.post(
            "/confirm",
            json={
                "action_id": "save-1",
                "action_type": "save",
                "approved": True,
                "session_id": "confirm-session",
            },
        ).json()

    assert first["ok"] is True
    assert first["status"] == "approved"
    assert first["remaining_actions"] == []
    assert "Action executed" in first["execution_result"]
    assert "Release Note" in first["memory_summary"]["summary"]

    assert second["ok"] is True
    assert second["status"] == "not_found"
    assert second["execution_result"] is None
    assert second["remaining_actions"] == []


def test_confirm_not_required_returns_standard_response_shape(tmp_path):
    app = create_app(settings=_settings(tmp_path / "not-required.db"))
    pending_action = {
        "action_id": "save-1",
        "action_type": "save",
        "description": "Save a note.",
        "payload": {"title": "Still Pending"},
    }

    with TestClient(app) as client:
        memory_store.ensure_session("read-session")
        memory_store.store_pending_actions("read-session", [pending_action])
        response = client.post(
            "/confirm",
            json={
                "action_id": "read-1",
                "action_type": "read",
                "approved": True,
                "session_id": "read-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"] == "not_required"
    assert payload["execution_result"] is None
    assert payload["remaining_actions"] == [pending_action]
    assert payload["memory_summary"]["session_id"] == "read-session"
