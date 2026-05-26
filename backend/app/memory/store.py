from __future__ import annotations

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
                        summary TEXT NOT NULL DEFAULT '',
                        workflow_state TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS research_references (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        captured_at TEXT NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                if demo_mode and self._is_empty(connection):
                    self._seed_demo_workflow(connection)
                connection.commit()

    def _is_empty(self, connection: sqlite3.Connection) -> bool:
        cursor = connection.execute("SELECT COUNT(*) FROM sessions;")
        session_count = cursor.fetchone()[0]
        return session_count == 0

    def _seed_demo_workflow(self, connection: sqlite3.Connection) -> None:
        now = _utc_now_iso()
        demo_session_id = "demo-session"
        connection.execute(
            """
            INSERT INTO sessions (session_id, summary, workflow_state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                demo_session_id,
                "Demo workflow seeded for hackathon judging mode.",
                '{"phase":"seeded"}',
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?), (?, ?, ?, ?);
            """,
            (
                demo_session_id,
                "user",
                "Resume my onboarding workflow from yesterday.",
                now,
                demo_session_id,
                "assistant",
                "Demo context restored. Ready to continue onboarding.",
                now,
            ),
        )

    def ensure_session(self, session_id: str | None = None) -> str:
        active_session_id = session_id or str(uuid4())
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO sessions (session_id, created_at, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET updated_at=excluded.updated_at;
                    """,
                    (active_session_id, now, now),
                )
                connection.commit()
        return active_session_id

    def append_message(self, session_id: str, role: str, content: str) -> None:
        now = _utc_now_iso()
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO messages (session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?);
                    """,
                    (session_id, role, content, now),
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

    def get_session_summary(self, session_id: str | None = None) -> dict:
        with self._lock:
            with self._connect() as connection:
                target_session_id = session_id or self._latest_session_id(connection)
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
                }

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


memory_store = MemoryStore()
