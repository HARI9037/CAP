import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "sessions.db")


def init_db():
    """Initializes the SQLite database structure for persisting session messages."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# Run database initializer on startup
init_db()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    state: Optional[Dict[str, Any]] = None
    pending_actions: Optional[List[Dict[str, Any]]] = None


@app.get("/ping")
async def ping_check():
    return {"status": "ok", "healthy": True}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # Fallback/Generate a clean unique string if it's a completely brand new session
    import uuid
    current_session = req.session_id if req.session_id else str(uuid.uuid4())

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message context empty")

    # 1. Persist User Message to SQLite Storage
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (current_session, "user", user_text)
        )
        conn.commit()

    # 2. CORE AGENT LOGIC (Your customized prompt generation / pipeline works here)
    # This is a sample mock reply structure. Replace this with your actual LLM / Prompt logic.
    ai_reply = f"Acknowledged. I have recorded your frame parameters: '{user_text}'"

    # Optional metadata frameworks for your application context layer
    mock_state = {"current_node": "session_sync", "active_context": "ready"}
    mock_actions = []

    # 3. Persist Assistant Response to SQLite Storage
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (current_session, "assistant", ai_reply)
        )
        conn.commit()

    return ChatResponse(
        reply=ai_reply,
        session_id=current_session,
        state=mock_state,
        pending_actions=mock_actions
    )


@app.get("/memory")
async def get_session_memory(session_id: str = Query(..., description="The unique session identifier string")):
    """Fetches the complete historical array log belonging to a distinct session."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            rows = cursor.fetchall()

            # Map SQL entries directly to standard React state schema formats
            history = [{"role": row["role"], "content": row["content"]}
                       for row in rows]
            return {"status": "success", "history": history}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database extraction failure: {str(e)}")


@app.delete("/memory")
async def delete_session_memory(session_id: str = Query(..., description="Session identifier targeted for erasure")):
    """Wipes out all corresponding historical messages matching the session ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()
            return {"status": "success", "message": f"Session {session_id} successfully wiped."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear session indices: {str(e)}")
