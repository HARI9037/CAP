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
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'local-user',
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
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        memory_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'local-user',
                        memory_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_session_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL DEFAULT 'local-user',
                        rating INTEGER NOT NULL,
                        comment TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        user_id TEXT PRIMARY KEY,
                        theme TEXT NOT NULL DEFAULT 'dark',
                        model TEXT NOT NULL DEFAULT 'gpt-5.5',
                        memory_enabled INTEGER NOT NULL DEFAULT 1,
                        confirmation_required INTEGER NOT NULL DEFAULT 1,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                self._ensure_session_schema(connection)
                self._ensure_message_schema(connection)
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp ON messages(session_id, timestamp);"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memories_user_type ON memories(user_id, memory_type);"
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
                INSERT INTO sessions (session_id, user_id, summary, workflow_state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    demo_session_id,
                    "local-user",
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

    def create_session(self, user_id: str, session_id: str | None = None) -> str:
        session_id = session_id or str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO sessions (session_id, user_id, summary, workflow_state, created_at, updated_at)
                    VALUES (?, ?, '', '{"phase": "general_chat", "state": "ready", "pending_actions": []}', ?, ?);
                    """,
                    (session_id, user_id, now, now),
                )
                connection.commit()
        return session_id

    def ensure_session(self, user_id: str, session_id: str | None = None) -> str:
        if session_id:
            with self._lock:
                with self._connect() as connection:
                    row = connection.execute("SELECT 1 FROM sessions WHERE session_id = ? AND user_id = ?;", (session_id, user_id)).fetchone()
                    if row:
                        return session_id
            return self.create_session(user_id=user_id, session_id=session_id)
        return self.create_session(user_id=user_id)

    def _ensure_session_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(sessions);").fetchall()
        }
        if "user_id" not in columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local-user';")
            
    def _ensure_message_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(messages);").fetchall()
        }
        now = _utc_now_iso()

        if "id" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN id INTEGER;")
            connection.execute(
                """
                UPDATE messages
                SET id = rowid
                WHERE id IS NULL;
                """
            )

        if "message_id" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN message_id TEXT;")

        if "timestamp" not in columns:
            connection.execute("ALTER TABLE messages ADD COLUMN timestamp TEXT;")

        if "created_at" in columns:
            connection.execute(
                """
                UPDATE messages
                SET timestamp = created_at
                WHERE timestamp IS NULL OR timestamp = '';
                """
            )

        connection.execute(
            """
            UPDATE messages
            SET timestamp = ?
            WHERE timestamp IS NULL OR timestamp = '';
            """,
            (now,),
        )

        rows = connection.execute(
            """
            SELECT rowid
            FROM messages
            WHERE message_id IS NULL OR message_id = '';
            """
        ).fetchall()
        for row in rows:
            connection.execute(
                """
                UPDATE messages
                SET message_id = ?
                WHERE rowid = ?;
                """,
                (str(uuid4()), row[0]),
            )

    def get_session_phase(self, session_id: str, user_id: str) -> str:
        with self._lock:
            with self._connect() as connection:
                state = self._read_workflow_state(connection, session_id, user_id)
                return state.get("phase", "general_chat")
                
    def append_message(self, session_id: str, role: str, content: str, user_id: str) -> None:
        message_id = str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                # Verify session ownership
                if not connection.execute("SELECT 1 FROM sessions WHERE session_id = ? AND user_id = ?;", (session_id, user_id)).fetchone():
                    raise ValueError("Session not found or access denied")
                    
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(messages);").fetchall()
                }
                insert_columns = [
                    "message_id",
                    "id",
                    "session_id",
                    "role",
                    "content",
                    "timestamp",
                ]
                values = [
                    message_id,
                    connection.execute(
                        "SELECT COALESCE(MAX(id), 0) + 1 FROM messages;"
                    ).fetchone()[0],
                    session_id,
                    role,
                    content,
                    now,
                ]
                if "created_at" in columns:
                    insert_columns.append("created_at")
                    values.append(now)

                placeholders = ", ".join("?" for _ in insert_columns)
                connection.execute(
                    f"""
                    INSERT INTO messages ({", ".join(insert_columns)})
                    VALUES ({placeholders});
                    """,
                    values,
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

    def get_session_history(self, session_id: str, user_id: str) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    SELECT m.role, m.content
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.session_id
                    WHERE m.session_id = ? AND s.user_id = ?
                    ORDER BY COALESCE(m.id, m.rowid) ASC, m.timestamp ASC;
                    """,
                    (session_id, user_id),
                )
                return [
                    {"role": row[0], "content": row[1]}
                    for row in cursor.fetchall()
                ]

    def delete_session(self, session_id: str, user_id: str) -> None:
        with self._lock:
            with self._connect() as connection:
                if not connection.execute("SELECT 1 FROM sessions WHERE session_id = ? AND user_id = ?;", (session_id, user_id)).fetchone():
                    return
                connection.execute(
                    "DELETE FROM messages WHERE session_id = ?;",
                    (session_id,),
                )
                connection.execute(
                    "DELETE FROM sessions WHERE session_id = ? AND user_id = ?;",
                    (session_id, user_id),
                )
                connection.commit()

    def list_sessions(self, user_id: str, query: str | None = None) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                sql = """
                    SELECT s.session_id, s.summary, s.created_at, s.updated_at, COUNT(m.message_id) as message_count
                    FROM sessions s
                    LEFT JOIN messages m ON m.session_id = s.session_id
                    WHERE s.user_id = ?
                """
                params: list[str] = [user_id]
                if query:
                    sql += " AND (s.summary LIKE ? OR s.session_id LIKE ?)"
                    like = f"%{query}%"
                    params.extend([like, like])
                sql += " GROUP BY s.session_id ORDER BY s.updated_at DESC;"
                rows = connection.execute(sql, params).fetchall()
                return [
                    {
                        "session_id": row[0],
                        "summary": row[1],
                        "created_at": row[2],
                        "updated_at": row[3],
                        "message_count": row[4],
                    }
                    for row in rows
                ]

    def get_session_messages(self, session_id: str, user_id: str) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT m.message_id, m.role, m.content, m.timestamp
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.session_id
                    WHERE m.session_id = ? AND s.user_id = ?
                    ORDER BY COALESCE(m.id, m.rowid) ASC, m.timestamp ASC;
                    """,
                    (session_id, user_id),
                ).fetchall()
                return [
                    {
                        "message_id": row[0],
                        "role": row[1],
                        "content": row[2],
                        "timestamp": row[3],
                    }
                    for row in rows
                ]

    def list_memories(self, user_id: str, memory_type: str | None = None) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                sql = """
                    SELECT memory_id, memory_type, title, content, source_session_id, created_at, updated_at
                    FROM memories
                    WHERE user_id = ?
                """
                params = [user_id]
                if memory_type:
                    sql += " AND memory_type = ?"
                    params.append(memory_type)
                sql += " ORDER BY updated_at DESC;"
                rows = connection.execute(sql, params).fetchall()
                return [
                    {
                        "memory_id": row[0],
                        "memory_type": row[1],
                        "title": row[2],
                        "content": row[3],
                        "source_session_id": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                    }
                    for row in rows
                ]

    def upsert_memory(
        self,
        title: str,
        content: str,
        memory_type: str,
        memory_id: str | None = None,
        user_id: str = "local-user",
        source_session_id: str | None = None,
    ) -> dict:
        now = _utc_now_iso()
        memory_id = memory_id or str(uuid4())
        with self._lock:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT created_at FROM memories WHERE memory_id = ? AND user_id = ?;",
                    (memory_id, user_id),
                ).fetchone()
                if existing:
                    connection.execute(
                        """
                        UPDATE memories
                        SET memory_type = ?, title = ?, content = ?, source_session_id = ?, updated_at = ?
                        WHERE memory_id = ? AND user_id = ?;
                        """,
                        (memory_type, title, content, source_session_id, now, memory_id, user_id),
                    )
                    created_at = existing[0]
                else:
                    connection.execute(
                        """
                        INSERT INTO memories (memory_id, user_id, memory_type, title, content, source_session_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (memory_id, user_id, memory_type, title, content, source_session_id, now, now),
                    )
                    created_at = now
                connection.commit()
        return {
            "memory_id": memory_id,
            "memory_type": memory_type,
            "title": title,
            "content": content,
            "source_session_id": source_session_id,
            "created_at": created_at,
            "updated_at": now,
        }

    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM memories WHERE memory_id = ? AND user_id = ?;",
                    (memory_id, user_id),
                )
                connection.commit()
                return cursor.rowcount > 0

    def add_feedback(self, rating: int, comment: str, user_id: str) -> dict:
        feedback_id = str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO feedback (feedback_id, user_id, rating, comment, created_at)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (feedback_id, user_id, rating, comment, now),
                )
                connection.commit()
        return {"feedback_id": feedback_id, "rating": rating, "comment": comment, "created_at": now}

    def get_settings(self, user_id: str) -> dict:
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT theme, model, memory_enabled, confirmation_required, updated_at
                    FROM settings
                    WHERE user_id = ?;
                    """,
                    (user_id,),
                ).fetchone()
                if row is None:
                    connection.execute(
                        """
                        INSERT INTO settings (user_id, theme, model, memory_enabled, confirmation_required, updated_at)
                        VALUES (?, 'dark', 'gpt-5.5', 1, 1, ?);
                        """,
                        (user_id, now),
                    )
                    connection.commit()
                    row = ("dark", "gpt-5.5", 1, 1, now)
                return {
                    "theme": row[0],
                    "model": row[1],
                    "memory_enabled": bool(row[2]),
                    "confirmation_required": bool(row[3]),
                    "updated_at": row[4],
                }

    def update_settings(self, updates: dict, user_id: str) -> dict:
        current = self.get_settings(user_id=user_id)
        merged = {**current, **updates}
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE settings
                    SET theme = ?, model = ?, memory_enabled = ?, confirmation_required = ?, updated_at = ?
                    WHERE user_id = ?;
                    """,
                    (
                        merged["theme"],
                        merged["model"],
                        int(bool(merged["memory_enabled"])),
                        int(bool(merged["confirmation_required"])),
                        now,
                        user_id,
                    ),
                )
                connection.commit()
        return {**merged, "updated_at": now}

    def _read_workflow_state(self, connection: sqlite3.Connection, session_id: str, user_id: str) -> dict:
        row = connection.execute(
            """
            SELECT workflow_state
            FROM sessions
            WHERE session_id = ? AND user_id = ?;
            """,
            (session_id, user_id),
        ).fetchone()
        if row is None:
            return {}
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            return {}

    def get_pending_actions(self, session_id: str, user_id: str) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                state = self._read_workflow_state(connection, session_id, user_id)
                return state.get("pending_actions") or []

    def store_pending_actions(self, session_id: str, user_id: str, actions: list[dict]) -> None:
        with self._lock:
            with self._connect() as connection:
                current_state = self._read_workflow_state(
                    connection, session_id, user_id)
                current_state["pending_actions"] = actions
                current_state["state"] = "awaiting_confirmation" if actions else "ready"

                now = _utc_now_iso()
                connection.execute(
                    """
                    UPDATE sessions
                    SET workflow_state = ?, updated_at = ?
                    WHERE session_id = ? AND user_id = ?;
                    """,
                    (json.dumps(current_state), now, session_id, user_id),
                )
                connection.commit()

    def resolve_pending_action(
        self,
        session_id: str,
        user_id: str,
        action_id: str,
    ) -> tuple[dict | None, list[dict]]:
        with self._lock:
            with self._connect() as connection:
                current_state = self._read_workflow_state(connection, session_id, user_id)
                pending_actions = current_state.get("pending_actions") or []
                if not isinstance(pending_actions, list):
                    pending_actions = []

                matched_action = None
                remaining_actions = []
                for action in pending_actions:
                    if (
                        matched_action is None
                        and isinstance(action, dict)
                        and action.get("action_id") == action_id
                    ):
                        matched_action = action
                        continue
                    if isinstance(action, dict):
                        remaining_actions.append(action)

                if matched_action is not None:
                    current_state["pending_actions"] = remaining_actions
                    current_state["state"] = (
                        "awaiting_confirmation" if remaining_actions else "ready"
                    )

                    now = _utc_now_iso()
                    connection.execute(
                        """
                        UPDATE sessions
                        SET workflow_state = ?, updated_at = ?
                        WHERE session_id = ? AND user_id = ?;
                        """,
                        (json.dumps(current_state), now, session_id, user_id),
                    )
                    connection.commit()

                return matched_action, remaining_actions

    def update_session_workflow_state(self, session_id: str, user_id: str, updates: dict) -> None:
        with self._lock:
            with self._connect() as connection:
                current_state = self._read_workflow_state(
                    connection, session_id, user_id)
                current_state.update(updates)

                now = _utc_now_iso()
                connection.execute(
                    """
                    UPDATE sessions
                    SET workflow_state = ?, updated_at = ?
                    WHERE session_id = ? AND user_id = ?;
                    """,
                    (json.dumps(current_state), now, session_id, user_id),
                )
                connection.commit()

    def update_session_summary(self, session_id: str, user_id: str, summary: str) -> None:
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE sessions
                    SET summary = ?, updated_at = ?
                    WHERE session_id = ? AND user_id = ?;
                    """,
                    (summary, now, session_id, user_id),
                )
                connection.commit()

    def _latest_session_id(self, connection: sqlite3.Connection, user_id: str) -> str | None:
        row = connection.execute(
            """
            SELECT session_id
            FROM sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1;
            """,
            (user_id,)
        ).fetchone()
        if row is None:
            return None
        return row[0]

    def get_session_summary(self, user_id: str, session_id: str | None = None) -> dict:
        with self._lock:
            with self._connect() as connection:
                target_session_id = session_id or self._latest_session_id(
                    connection, user_id)
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
                    WHERE session_id = ? AND user_id = ?;
                    """,
                    (target_session_id, user_id),
                ).fetchone()
                message_count = connection.execute(
                    """
                    SELECT COUNT(m.message_id)
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.session_id
                    WHERE m.session_id = ? AND s.user_id = ?;
                    """,
                    (target_session_id, user_id),
                ).fetchone()[0]
                return {
                    "session_id": target_session_id,
                    "summary": summary_row[0] if summary_row else "",
                    "message_count": message_count,
                    "updated_at": summary_row[1] if summary_row else None,
                    "workflow_state": self._read_workflow_state(connection, target_session_id, user_id),
                }


memory_store = MemoryStore()
