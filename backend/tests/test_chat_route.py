import sqlite3
import json

import httpx
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


def _stored_messages(db_path, session_id):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC;
            """,
            (session_id,),
        ).fetchall()


def _workflow_state(db_path, session_id):
    with sqlite3.connect(db_path) as connection:
        raw_state = connection.execute(
            """
            SELECT workflow_state
            FROM sessions
            WHERE session_id = ?;
            """,
            (session_id,),
        ).fetchone()[0]
    return json.loads(raw_state)


def test_chat_endpoint_returns_validated_groq_reply_and_stores_conversation(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "chat.db"

    def fake_groq_call(session_history, current_phase, settings):
        assert session_history[-1] == {"role": "user", "content": "Hello CAP"}
        assert current_phase == "general_chat"
        assert settings.groq_api_key == "test-key"
        return json.dumps({"reply": "Hello. I am CAP.", "pending_actions": []})

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Hello CAP", "session_id": "session-1"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["session_id"] == "session-1"
    assert payload["reply"] == "Hello. I am CAP."
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"
    assert payload["error"] is None
    assert _stored_messages(db_path, "session-1") == [
        ("user", "Hello CAP"),
        ("assistant", "Hello. I am CAP."),
    ]
    assert _workflow_state(db_path, "session-1")["state"] == "ready"


def test_chat_endpoint_stores_pending_actions_and_awaits_confirmation(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "actions.db"
    action = {
        "action_id": "action-1",
        "action_type": "update",
        "description": "Update the architecture diagram.",
        "payload": {"target_resource": "diagram", "parameters": {}},
    }

    def fake_groq_call(session_history, current_phase, settings):
        return json.dumps(
            {
                "reply": "I can prepare that update for your approval.",
                "pending_actions": [action],
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Update the diagram.", "session_id": "session-actions"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["state"] == "awaiting_confirmation"
    assert payload["pending_actions"] == [action]
    state = _workflow_state(db_path, "session-actions")
    assert state["state"] == "awaiting_confirmation"
    assert state["pending_actions"] == [action]


def test_chat_endpoint_surfaces_roadmap_payload_in_chat(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "roadmap-payload.db"
    roadmap = (
        "3-Day Roadmap for Building an Admin Dashboard\n\n"
        "Day 1: Define roles, database tables, and attendance entry screens.\n"
        "Day 2: Build teacher workflows, attendance APIs, and dashboard filters.\n"
        "Day 3: Add reports, polish validation, test deployment, and fix edge cases."
    )
    action = {
        "action_id": "roadmap-1",
        "action_type": "write",
        "description": "Write the 3-day roadmap.",
        "payload": {
            "title": "3-Day Roadmap",
            "content": roadmap,
        },
    }

    def fake_groq_call(session_history, current_phase, settings):
        return json.dumps(
            {
                "reply": "3-Day Roadmap for Building an Admin Dashboard",
                "pending_actions": [action],
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": "give me the road map here in the chat",
                "session_id": "roadmap-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["reply"] == roadmap
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"
    assert _workflow_state(db_path, "roadmap-session")["pending_actions"] == []


def test_chat_endpoint_suppresses_unrequested_update_actions(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "unrequested-updates.db"
    actions = [
        {
            "action_id": "schema-1",
            "action_type": "update",
            "description": "Define the database schema for attendance tracking.",
            "payload": {"target_resource": "session", "parameters": {}},
        },
        {
            "action_id": "realtime-1",
            "action_type": "update",
            "description": "Explore real-time attendance tracking options.",
            "payload": {"target_resource": "session", "parameters": {}},
        },
    ]

    def fake_groq_call(session_history, current_phase, settings):
        return json.dumps(
            {
                "reply": (
                    "That's an exciting project. Consider real-time attendance "
                    "tracking, automatic record keeping, and analytics."
                ),
                "pending_actions": actions,
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": "I want to build a webapp for tracking attendance.",
                "session_id": "feature-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"
    assert _workflow_state(db_path, "feature-session")["pending_actions"] == []


def test_chat_endpoint_keeps_explicit_pending_queue_actions(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "explicit-queue.db"
    actions = [
        {
            "action_id": "component-1",
            "action_type": "update",
            "description": "Build the NavigationHeader component.",
            "payload": {
                "target_resource": "project planning queue",
                "content": "Build the NavigationHeader component.",
            },
        },
        {
            "action_id": "component-2",
            "action_type": "update",
            "description": "Build the DashboardPage component.",
            "payload": {
                "target_resource": "project planning queue",
                "content": "Build the DashboardPage component.",
            },
        },
    ]

    def fake_groq_call(session_history, current_phase, settings):
        return json.dumps(
            {
                "reply": (
                    "Start with NavigationHeader, DashboardPage, and ProjectCard. "
                    "I queued the first two components for approval."
                ),
                "pending_actions": actions,
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": (
                    "Initialize the structure, identify the first three priority "
                    "components, and place them in the pending actions queue "
                    "for my approval."
                ),
                "session_id": "explicit-queue-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["state"] == "awaiting_confirmation"
    assert payload["pending_actions"] == actions
    assert _workflow_state(db_path, "explicit-queue-session")["pending_actions"] == actions


def test_chat_endpoint_completes_cut_off_reply_with_pending_actions(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "cutoff-reply.db"
    calls = []
    actions = [
        {
            "action_id": "plan-1",
            "action_type": "update",
            "description": "Dashboard: displaying tasks and projects.",
            "payload": {
                "target_resource": "project planning queue",
                "content": "Dashboard: displaying tasks and projects.",
            },
        },
        {
            "action_id": "plan-2",
            "action_type": "update",
            "description": "Authentication: for user sign-up and login.",
            "payload": {
                "target_resource": "project planning queue",
                "content": "Authentication: for user sign-up and login.",
            },
        },
    ]
    full_reply = (
        "Based on our current requirements, I've determined an MVP approach with the following components:\n\n"
        "1. Dashboard: displaying tasks and projects.\n"
        "2. Authentication: for user sign-up and login.\n"
        "3. Task Form: for creating and editing tasks.\n\n"
        "Below are the components I recommend prioritizing first, starting with the dashboard and auth flow."
    )

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": "Based on our current requirements, I've determined an MVP approach with the following components:\n\n1. Dashboard: displaying tasks and projects.\n1. Authentication: for user sign-up and login.\n1. Task Form: for creating and editing tasks.\n\nBelow are the",
                    "pending_actions": actions,
                }
            )
        return json.dumps({"reply": full_reply, "pending_actions": actions})

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": (
                    "I am starting a new web app project using React and Tailwind. "
                    "My goal is to build a project management dashboard. Please "
                    "initialize the structure, identify the first three priority "
                    "components I should build, and place them in the pending "
                    "actions queue for my approval."
                ),
                "session_id": "cutoff-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(calls) == 2
    assert payload["state"] == "awaiting_confirmation"
    assert payload["pending_actions"] == actions
    assert "Below are the components" in payload["reply"]
    assert payload["reply"].endswith("auth flow.")


def test_chat_endpoint_retries_missing_explicit_queue_actions(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "queue-retry.db"
    calls = []
    actions = [
        {
            "action_id": "auth-1",
            "action_type": "update",
            "description": "Define authentication goals and requirements.",
            "payload": {
                "target_resource": "approval queue",
                "content": "Define authentication goals and requirements.",
            },
        },
        {
            "action_id": "auth-2",
            "action_type": "update",
            "description": "Choose the authentication method.",
            "payload": {
                "target_resource": "approval queue",
                "content": "Choose the authentication method.",
            },
        },
    ]

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": (
                        "Define authentication goals and requirements\n"
                        "Choose authentication method\n"
                        "Implement authentication API"
                    ),
                    "pending_actions": [],
                }
            )
        return json.dumps(
            {
                "reply": "I placed the authentication plan into the approval queue.",
                "pending_actions": actions,
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": (
                    "Generate the authentication modules as a plan but do not "
                    "execute anything until I explicitly approve each action."
                ),
                "session_id": "queue-retry-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(calls) == 2
    assert payload["state"] == "awaiting_confirmation"
    assert payload["pending_actions"] == actions
    assert "Implement authentication API" in payload["reply"]


def test_chat_endpoint_synthesizes_queue_when_model_omits_actions(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "queue-synthesize.db"
    calls = []

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": (
                        "1. Define authentication goals and requirements\n"
                        "2. Choose authentication method\n"
                        "3. Implement authentication API"
                    ),
                    "pending_actions": [],
                }
            )
        raise httpx.TimeoutException("retry timed out")

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": (
                    "Generate the authentication modules as a plan but do not "
                    "execute anything until I explicitly approve each action."
                ),
                "session_id": "queue-synthesize-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(calls) == 2
    assert payload["state"] == "awaiting_confirmation"
    assert len(payload["pending_actions"]) == 3
    assert payload["pending_actions"][0]["action_type"] == "update"
    assert "Define authentication goals" in payload["pending_actions"][0]["description"]


def test_chat_endpoint_synthesizes_save_memory_action(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "save-memory-synthesize.db"
    calls = []

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": "React was replaced with Vue for the dashboard plan.",
                    "pending_actions": [],
                }
            )
        raise httpx.TimeoutException("retry timed out")

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": "savethis, in your memory",
                "session_id": "save-memory-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["state"] == "awaiting_confirmation"
    assert len(payload["pending_actions"]) == 1
    assert payload["pending_actions"][0]["action_type"] == "save"
    assert "React was replaced with Vue" in payload["pending_actions"][0]["description"]


def test_chat_endpoint_retries_thin_techstack_reply(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "techstack-retry.db"
    calls = []
    full_reply = (
        "For a beginner-friendly attendance dashboard, use React with Vite "
        "for the frontend, FastAPI for the backend, PostgreSQL for data, "
        "JWT auth for teacher logins, and Vercel plus Render for deployment.\n\n"
        "1. React + Vite: simple component development and quick builds.\n"
        "2. FastAPI: clean API structure and automatic validation.\n"
        "3. PostgreSQL: reliable attendance records and reporting queries."
    )

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": "For your project, I recommend the following tech stack:",
                    "pending_actions": [
                        {
                            "action_id": "techstack-1",
                            "action_type": "update",
                            "description": "Update the session with a tech stack.",
                            "payload": {"target_resource": "session"},
                        }
                    ],
                }
            )
        return json.dumps({"reply": full_reply, "pending_actions": []})

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": (
                    "I'm a complete beginner. Give me a detailed techstack "
                    "list and why you choose that."
                ),
                "session_id": "techstack-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(calls) == 2
    assert payload["reply"] == full_reply
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"


def test_chat_endpoint_treats_memory_recall_as_informational_and_completes_cutoff(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "memory-recall-cutoff.db"
    calls = []
    full_reply = (
        "In this session, we discussed CAP as a context-aware assistant, "
        "covered memory, action approvals, deployment planning, and generated "
        "a deployment checklist with backend and frontend readiness steps."
    )

    def fake_groq_call(session_history, current_phase, settings):
        calls.append(session_history)
        if len(calls) == 1:
            return json.dumps(
                {
                    "reply": (
                        "In this session, we discussed CAP as a context-aware "
                        "assistant and generated a deployment checklist with"
                    ),
                    "pending_actions": [],
                }
            )
        return json.dumps({"reply": full_reply, "pending_actions": []})

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "message": "What do you remember from this session?",
                "session_id": "memory-recall-session",
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert len(calls) == 2
    assert payload["reply"] == full_reply
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"
    assert _workflow_state(db_path, "memory-recall-session")["pending_actions"] == []


def test_chat_endpoint_respects_architecture_review_phase(tmp_path, monkeypatch):
    db_path = tmp_path / "architecture-review.db"

    def fake_groq_call(session_history, current_phase, settings):
        assert current_phase == "architecture_review"
        assert session_history[-1] == {
            "role": "user",
            "content": "Review the load balancer.",
        }
        return json.dumps(
            {
                "reply": "The load balancer setup looks ready for review.",
                "pending_actions": [],
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        memory_store.ensure_session("architecture-session")
        memory_store.update_session_workflow_state(
            "architecture-session",
            {"phase": "architecture_review"},
        )
        response = client.post(
            "/chat",
            json={
                "message": "Review the load balancer.",
                "session_id": "architecture-session",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["state"] == "ready"
    assert payload["pending_actions"] == []
    assert _workflow_state(db_path, "architecture-session")["phase"] == "architecture_review"


def test_chat_endpoint_sends_compressed_memory_without_extra_system_messages(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "compressed-context.db"

    def fake_groq_call(session_history, current_phase, settings):
        assert current_phase == "general_chat"
        assert session_history[0]["role"] == "assistant"
        assert session_history[0]["content"].startswith("Earlier session summary:")
        assert all(message["role"] != "system" for message in session_history)
        assert session_history[-1] == {
            "role": "user",
            "content": "Message 16",
        }
        return json.dumps(
            {
                "reply": "Context is still coherent.",
                "pending_actions": [],
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        memory_store.ensure_session("long-session")
        for index in range(15):
            role = "user" if index % 2 == 0 else "assistant"
            memory_store.append_message("long-session", role, f"Message {index + 1}")
        response = client.post(
            "/chat",
            json={"message": "Message 16", "session_id": "long-session"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["reply"] == "Context is still coherent."


def test_chat_endpoint_expands_context_for_memory_recall(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "expanded-recall-context.db"

    def fake_groq_call(session_history, current_phase, settings):
        assert current_phase == "general_chat"
        assert session_history[0]["role"] == "assistant"
        assert session_history[0]["content"].startswith("Earlier session summary:")
        assert "Message 1" in session_history[0]["content"]
        assert len(session_history) == 41
        assert session_history[1] == {"role": "assistant", "content": "Message 6"}
        assert session_history[-1] == {
            "role": "user",
            "content": "What do you remember from this session?",
        }
        return json.dumps(
            {
                "reply": "I can recall the broader session context.",
                "pending_actions": [],
            }
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", fake_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        memory_store.ensure_session("expanded-recall-session")
        for index in range(44):
            role = "user" if index % 2 == 0 else "assistant"
            memory_store.append_message(
                "expanded-recall-session",
                role,
                f"Message {index + 1}",
            )
        response = client.post(
            "/chat",
            json={
                "message": "What do you remember from this session?",
                "session_id": "expanded-recall-session",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["reply"] == "I can recall the broader session context."


def test_chat_endpoint_returns_fallback_on_groq_timeout(tmp_path, monkeypatch):
    db_path = tmp_path / "timeout.db"

    def timeout_groq_call(session_history, current_phase, settings):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", timeout_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"prompt": "Are you there?", "session_id": "session-2"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["session_id"] == "session-2"
    assert payload["error"] == "groq_timeout"
    assert payload["state"] == "fallback"
    assert payload["reply"]
    assert len(_stored_messages(db_path, "session-2")) == 2
    assert _workflow_state(db_path, "session-2")["phase"] == "fallback"


def test_chat_endpoint_returns_plain_text_llm_response(tmp_path, monkeypatch):
    db_path = tmp_path / "plain-text.db"

    def plain_text_groq_call(session_history, current_phase, settings):
        return "Here is a focused six-hour execution plan."

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", plain_text_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Please make a plan.", "session_id": "session-3"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["session_id"] == "session-3"
    assert payload["reply"] == "Here is a focused six-hour execution plan."
    assert payload["error"] is None
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"


def test_chat_endpoint_extracts_message_from_jsonish_llm_response(tmp_path, monkeypatch):
    db_path = tmp_path / "jsonish-message.db"

    def jsonish_groq_call(session_history, current_phase, settings):
        return (
            '{"message":"Here is your prep material.\n'
            'Focus on the demo first.\n\n'
            '**Pending Actions: []"}'
        )

    monkeypatch.setattr("app.orchestrator.service._call_groq_api", jsonish_groq_call)
    app = create_app(settings=_settings(db_path))

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Give prep material.", "session_id": "session-jsonish"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["reply"] == "Here is your prep material.\nFocus on the demo first."
    assert payload["pending_actions"] == []
    assert payload["state"] == "ready"


def test_chat_endpoint_returns_fallback_when_groq_key_is_missing(tmp_path):
    db_path = tmp_path / "missing-key.db"
    settings = _settings(db_path)
    settings = Settings(
        app_name=settings.app_name,
        app_version=settings.app_version,
        log_level=settings.log_level,
        demo_mode=settings.demo_mode,
        db_path=settings.db_path,
        cors_origins=settings.cors_origins,
        groq_api_key=None,
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Hello", "session_id": "missing-key-session"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["state"] == "fallback"
    assert payload["error"] == "groq_configuration_missing"
