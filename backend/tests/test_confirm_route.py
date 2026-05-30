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


def test_confirm_alias_action_type_resolves_pending_action(tmp_path):
    app = create_app(settings=_settings(tmp_path / "alias-confirm.db"))
    action = {
        "action_id": "create-1",
        "action_type": "create_note",
        "description": "Create a note from this session.",
        "payload": {
            "title": "Aliased Note",
            "content": "Alias action types should still execute.",
        },
    }

    with TestClient(app) as client:
        memory_store.ensure_session("alias-session")
        memory_store.store_pending_actions("alias-session", [action])
        response = client.post(
            "/confirm",
            json={
                "action_id": "create-1",
                "action_type": "create_note",
                "approved": True,
                "session_id": "alias-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "approved"
    assert payload["remaining_actions"] == []
    assert "Action executed" in payload["execution_result"]
    assert "Aliased Note" in payload["memory_summary"]["summary"]


def test_confirm_approved_update_returns_visible_description(tmp_path):
    app = create_app(settings=_settings(tmp_path / "visible-update.db"))
    action = {
        "action_id": "update-1",
        "action_type": "update",
        "description": "Define the database schema for attendance tracking.",
        "payload": {"target_resource": "session", "parameters": {}},
    }

    with TestClient(app) as client:
        memory_store.ensure_session("visible-update-session")
        memory_store.store_pending_actions("visible-update-session", [action])
        response = client.post(
            "/confirm",
            json={
                "action_id": "update-1",
                "action_type": "update",
                "approved": True,
                "session_id": "visible-update-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "approved"
    assert payload["remaining_actions"] == []
    assert "Action executed" in payload["execution_result"]
    assert "Define the database schema" in payload["execution_result"]


def test_confirm_rejection_returns_visible_result(tmp_path):
    app = create_app(settings=_settings(tmp_path / "visible-reject.db"))
    action = {
        "action_id": "reject-1",
        "action_type": "update",
        "description": "Explore real-time attendance tracking options.",
        "payload": {"target_resource": "session", "parameters": {}},
    }

    with TestClient(app) as client:
        memory_store.ensure_session("visible-reject-session")
        memory_store.store_pending_actions("visible-reject-session", [action])
        response = client.post(
            "/confirm",
            json={
                "action_id": "reject-1",
                "action_type": "update",
                "approved": False,
                "session_id": "visible-reject-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "rejected"
    assert payload["remaining_actions"] == []
    assert "Action rejected" in payload["execution_result"]
    assert "real-time attendance" in payload["execution_result"]


def test_confirm_pending_read_like_action_still_resolves(tmp_path):
    app = create_app(settings=_settings(tmp_path / "pending-read.db"))
    action = {
        "action_id": "custom-1",
        "action_type": "custom_review",
        "description": "Review a session note.",
        "payload": {"target_resource": "session note"},
    }

    with TestClient(app) as client:
        memory_store.ensure_session("custom-session")
        memory_store.store_pending_actions("custom-session", [action])
        response = client.post(
            "/confirm",
            json={
                "action_id": "custom-1",
                "action_type": "custom_review",
                "approved": True,
                "session_id": "custom-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "approved"
    assert payload["remaining_actions"] == []
    assert "Action executed" in payload["execution_result"]
