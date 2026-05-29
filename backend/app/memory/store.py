from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class MemoryStore:
    def __init__(self) -> None:
        self._db_path: Path | None = None
        self._lock = Lock()

    @property
    def db_path(self) -> Path:
        if self._db_path is None:
            raise RuntimeError("Memory store is not initialized.")
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def initialize(self, db_path: Path, demo_mode: bool = False) -> None:
        with self._lock:
            self._db_path = db_path
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (\n                        session_id TEXT PRIMARY KEY,
                        summary TEXT NOT NULL DEFAULT '',
                        workflow_state TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (\n                        message_id TEXT PRIMARY KEY,
                        id INTEGER,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    );
                    """
                )
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(messages);").fetchall()
                }
                if "id" not in columns:
                    connection.execute("ALTER TABLE messages ADD COLUMN id INTEGER;")
                    connection.execute(
                        """
                        UPDATE messages
                        SET id = rowid
                        WHERE id IS NULL;
                        """
                    )
                connection.commit()

            if demo_mode:
                self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM sessions;").fetchone()
            if row and row[0] > 0:
                return

            demo_session_id = "demo-session-001"
            now = _utc_now_iso()

            demo_workflow = {
                "state": "awaiting_confirmation",
                "pending_actions": [
                    {
                        "action_id": "act-991",
                        "action_type": "write",
                        "description": "Create background architectural specifications tracking file.",
                        "payload": {
                            "path": "docs/ORCHESTRATION_SPEC.md",
                            "content": "# Interception Core\nTracking system verification rules."
                        }
                    }
                ]
            }

            connection.execute(
                """
                INSERT INTO sessions (session_id, summary, workflow_state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    demo_session_id,
                    "Reviewing core terminal system configuration and interceptor loop limits.",
                    json.dumps(demo_workflow),
                    now,
                    now,
                ),
            )

            messages = [
                ("msg-1", "user",
                 "Can you help me initialize the core pipeline verification docs?"),
                ("msg-2", "assistant", "Sure, I've staged an action to build out your validation tracking layer. Please confirm the payload execution."),
            ]
            for msg_id, role, content in messages:
                connection.execute(
                    """
                    INSERT INTO messages (message_id, id, session_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (msg_id, None, demo_session_id, role, content, now),
                )
            connection.commit()

    def create_session(self, session_id: str | None = None) -> str:
        session_id = session_id or str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO sessions (session_id, summary, workflow_state, created_at, updated_at)
                    VALUES (?, '', '{"phase": "general_chat", "state": "ready", "pending_actions": []}', ?, ?);
                    """,
                    (session_id, now, now),
                )
                connection.commit()
        return session_id
    def ensure_session(self, session_id: str | None = None) -> str:
        if session_id:
            with self._lock:
                with self._connect() as connection:
                    row = connection.execute("SELECT 1 FROM sessions WHERE session_id = ?;", (session_id,)).fetchone()
                    if row:
                        return session_id
            return self.create_session(session_id=session_id)
        return self.create_session()

    def get_session_phase(self, session_id: str) -> str:
        with self._lock:
            with self._connect() as connection:
                state = self._read_workflow_state(connection, session_id)
                return state.get("phase", "general_chat")
                
    def append_message(self, session_id: str, role: str, content: str) -> None:
        message_id = str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO messages (message_id, id, session_id, role, content, timestamp)
                    VALUES (
                        ?,
                        (SELECT COALESCE(MAX(id), 0) + 1 FROM messages),
                        ?,
                        ?,
                        ?,
                        ?
                    );
                    """,
                    (message_id, session_id, role, content, now),
                )
                connection.execute(
                    """
                    UPDATE sessions
                    SET updated_at = ?
                    WHERE session_id = ?;
                    """,
                    (now, session_id),
                )
                connection.commit()

    def get_session_history(self, session_id: str) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY timestamp ASC;
                    """,
                    (session_id,),
                )
                return [
                    {"role": row[0], "content": row[1]}
                    for row in cursor.fetchall()
                ]

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM messages WHERE session_id = ?;",
                    (session_id,),
                )
                connection.execute(
                    "DELETE FROM sessions WHERE session_id = ?;",
                    (session_id,),
                )
                connection.commit()

    def _read_workflow_state(self, connection: sqlite3.Connection, session_id: str) -> dict:
        row = connection.execute(
            """
            SELECT workflow_state
            FROM sessions
            WHERE session_id = ?;
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            return {}
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            return {}

    def get_pending_actions(self, session_id: str) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                state = self._read_workflow_state(connection, session_id)
                return state.get("pending_actions") or []

    def store_pending_actions(self, session_id: str, actions: list[dict]) -> None:
        with self._lock:
            with self._connect() as connection:
                current_state = self._read_workflow_state(
                    connection, session_id)
                current_state["pending_actions"] = actions
                current_state["state"] = "awaiting_confirmation" if actions else "ready"

                now = _utc_now_iso()
                connection.execute(
                    """
                    UPDATE sessions
                    SET workflow_state = ?, updated_at = ?
                    WHERE session_id = ?;
                    """,
                    (json.dumps(current_state), now, session_id),
                )
                connection.commit()

    def update_session_workflow_state(self, session_id: str, updates: dict) -> None:
        with self._lock:
            with self._connect() as connection:
                current_state = self._read_workflow_state(
                    connection, session_id)
                current_state.update(updates)

                now = _utc_now_iso()
                connection.execute(
                    """
                    UPDATE sessions
                    SET workflow_state = ?, updated_at = ?
                    WHERE session_id = ?;
                    """,
                    (json.dumps(current_state), now, session_id),
                )
                connection.commit()

    def update_session_summary(self, session_id: str, summary: str) -> None:
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE sessions
                    SET summary = ?, updated_at = ?
                    WHERE session_id = ?;
                    """,
                    (summary, now, session_id),
                )
                connection.commit()

    def _latest_session_id(self, connection: sqlite3.Connection) -> str | None:
        row = connection.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT 1;
            """
        ).fetchone()
        if row is None:
            return None
        return row[0]

    def get_session_summary(self, session_id: str | None = None) -> dict:
        with self._lock:
            with self._connect() as connection:
                target_session_id = session_id or self._latest_session_id(
                    connection)
                if target_session_id is None:
                    return {
                        "session_id": None,
                        "summary": "",
                        "message_count": 0,
                        "updated_at": None,
                    }
                summary_row = connection.execute(
                    """
                    SELECT summary, updated_at
                    FROM sessions
                    WHERE session_id = ?;
                    """,
                    (target_session_id,),
                ).fetchone()
                message_count = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM messages
                    WHERE session_id = ?;
                    """,
                    (target_session_id,),
                ).fetchone()[0]
                return {
                    "session_id": target_session_id,
                    "summary": summary_row[0] if summary_row else "",
                    "message_count": message_count,
                    "updated_at": summary_row[1] if summary_row else None,
                    "workflow_state": self._read_workflow_state(connection, target_session_id),
                }


memory_store = MemoryStore()
