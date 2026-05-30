import sqlite3
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.memory.store import memory_store
from app.utils.env import Settings
from main import create_app


def _count_sessions(db_path):
    with sqlite3.connect(db_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM sessions;").fetchone()[0]


def test_memory_initializes_without_demo_seed(tmp_path):
    db_path = tmp_path / "plain.db"
    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert _count_sessions(db_path) == 0


def test_memory_initializes_with_demo_seed_when_enabled(tmp_path):
    db_path = tmp_path / "seeded.db"
    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=True,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert _count_sessions(db_path) == 1


def test_memory_initialization_migrates_legacy_message_schema(tmp_path):
    db_path = tmp_path / "legacy.db"
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL DEFAULT '',
                workflow_state TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.execute(
            """
            INSERT INTO sessions (session_id, summary, workflow_state, created_at, updated_at)
            VALUES (?, '', ?, ?, ?);
            """,
            (
                "legacy-session",
                json.dumps(
                    {
                        "phase": "general_chat",
                        "state": "ready",
                        "pending_actions": [],
                    }
                ),
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?);
            """,
            ("legacy-session", "user", "Existing legacy message.", now),
        )
        connection.commit()

    settings = Settings(
        app_name="CAP Backend",
        app_version="0.1.0",
        log_level="INFO",
        demo_mode=False,
        db_path=db_path,
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        memory_store.append_message(
            "legacy-session",
            "assistant",
            "New message after migration.",
        )

    assert memory_store.get_session_history("legacy-session") == [
        {"role": "user", "content": "Existing legacy message."},
        {"role": "assistant", "content": "New message after migration."},
    ]
