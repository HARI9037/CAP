import os
import sqlite3
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from groq import Groq
from backend.app.api.chat import router as chat_router

app = FastAPI()

app.include_router(chat_router)

# Enable CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cap-mvp.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq Client
# Ensure you have set GROQ_API_KEY in Render Dashboard -> Environment
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DB_PATH = os.path.join(os.path.dirname(__file__), "sessions.db")


def init_db():
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


@app.get("/health")
async def health_check():
    return {"status": "ok", "healthy": True}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    current_session = req.session_id if req.session_id else str(uuid.uuid4())
    user_text = req.message.strip()

    if not user_text:
        raise HTTPException(status_code=400, detail="Message context empty")

    # 1. Save User Message to Database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (current_session, "user", user_text)
        )
        conn.commit()

    # 2. Build Context from History
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (current_session,)
        )
        rows = cursor.fetchall()
        messages = [
            {"role": "system", "content": "You are CAP, a helpful, context-aware operational partner."}]
        for row in rows:
            messages.append({"role": row["role"], "content": row["content"]})

    # 3. Get AI Response from Groq
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=messages,
            temperature=0.7,
        )
        ai_reply = completion.choices[0].message.content
    except Exception as e:
        ai_reply = "I'm having trouble connecting to my processing core right now. Please try again."
        print(f"Groq API Error: {e}")

    # 4. Save AI Response
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
        state={"status": "ready"},
        pending_actions=[]
    )


@app.get("/memory")
async def get_session_memory(session_id: str = Query(...)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        history = [{"role": row["role"], "content": row["content"]}
                   for row in cursor.fetchall()]
    return {"status": "success", "history": history}


@app.delete("/memory")
async def delete_session_memory(session_id: str = Query(...)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
    return {"status": "success"}
