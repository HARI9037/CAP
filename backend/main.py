import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

app = FastAPI()

# ---------------------------------------------------------
# 1. CORS CONFIGURATION (Allows Netlify to talk to Render)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you can change this to "https://cap-mvp.netlify.app"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 2. DATABASE SETUP
# ---------------------------------------------------------
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

init_db()

# ---------------------------------------------------------
# 3. DATA MODELS
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    state: Optional[Dict[str, Any]] = None
    pending_actions: Optional[List[Dict[str, Any]]] = None

# ---------------------------------------------------------
# 4. API ENDPOINTS
# ---------------------------------------------------------

@app.get("/ping")
async def ping_check():
    """Health check endpoint renamed to /ping to bypass adblockers on the frontend."""
    return {"status": "ok", "healthy": True}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # Determine the session ID
    current_session = req.session_id if req.session_id else str(uuid.uuid4())
    user_text = req.message.strip()
    
    if not user_text:
        raise HTTPException(status_code=400, detail="Message context empty")

    # STEP A: Save the User's message to the database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (current_session, "user", user_text)
        )
        conn.commit()

    # =====================================================================
    # STEP B: 🧠 YOUR ACTUAL AI LOGIC GOES HERE 🧠
    # =====================================================================
    # Replace the code below with your actual API calls (OpenAI, Gemini, etc.)
    # Example: 
    # response = openai.ChatCompletion.create(messages=your_history, model="gpt-4")
    # ai_reply = response.choices[0].message.content
    
    # -> For now, I am making it echo a slightly smarter response so you know it works:
    if "hello" in user_text.lower() or "hi" in user_text.lower():
        ai_reply = "Hello! I am CAP, your Context-Aware Partner. My database is connected, but my LLM brain needs to be wired up by you!"
    else:
        ai_reply = f"You just said: '{user_text}'. (Replace this block in main.py with your LLM integration)."
    
    mock_state = {"current_node": "active", "status": "LLM not connected yet"}
    mock_actions = []
    # =====================================================================

    # STEP C: Save the AI's response to the database
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
            
            history = [{"role": row["role"], "content": row["content"]} for row in rows]
            return {"status": "success", "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database extraction failure: {str(e)}")


@app.delete("/memory")
async def delete_session_memory(session_id: str = Query(..., description="Session identifier targeted for erasure")):
    """Wipes out all corresponding historical messages matching the session ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()
            return {"status": "success", "message": f"Session {session_id} successfully wiped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session indices: {str(e)}")