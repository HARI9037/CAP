# backend/

## Purpose

FastAPI backend for CAP (Context-Aware Partner).
It handles chat orchestration, SQLite-backed session memory, Groq API calls, health checks, and confirmation state for pending actions.
Confirmed `save` and `write` actions execute the session-note tool and update the session summary. Other mutating actions are acknowledged without side effects.

## Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- Groq API model: `llama-3.1-8b-instant`
- `httpx` synchronous HTTP client
- SQLite via Python built-in `sqlite3`
- `python-dotenv` with `dotenv_values`
- Render backend hosting
- React + Vite + Tailwind CSS frontend hosted on Netlify

## Core Philosophy

THINK IN CLOUD -> ACT LOCALLY -> CONFIRM EVERYTHING

- Cloud: Groq reasons and proposes structured actions.
- Local: SQLite stores session history, workflow state, and pending actions.
- Confirm: mutating actions require explicit approval through `POST /confirm`.

Mutating action types:

- `write`
- `update`
- `organize`
- `save`
- `delete`

## Architecture Overview

Entry point:

- `main.py`
- `create_app(settings)`
- Routers mounted: `health`, `chat`, `confirm`, `memory`
- `memory_store.initialize()` runs with `db_path` and `demo_mode` from settings
- CORS is configured from `settings.cors_origins`

`POST /chat` request flow:

1. `app/routes/chat.py` validates the request.
2. The route delegates to `process_chat_message()` in `app/orchestrator/service.py`.
3. The orchestrator calls `memory_store.ensure_session()`.
4. The user message is appended to SQLite.
5. The context builder loads the current phase, recent history, and compressed older memory from SQLite.
6. The system prompt is loaded from `docs/ORCHESTRATION_SPEC.md`.
7. Groq is called through `httpx.Client` with `response_format: {"type": "json_object"}`.
8. The response is parsed into `LLMResponse(reply, pending_actions[])`.
9. The assistant reply is stored in SQLite.
10. Pending actions are stored and state becomes `awaiting_confirmation`, or state remains `ready`.
11. A `ChatResult` is returned to the route and sent to the frontend.

Fallback behavior:

- `TimeoutException`, `HTTPStatusError`, JSON parse errors, and validation errors return safe replies.
- Fallbacks update the session workflow state to `fallback`.
- These failures do not crash the API route.

## API Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns backend readiness from `get_health_status()`. |
| `GET` | `/ping` | Health-compatible endpoint with `healthy: true`. |
| `POST` | `/chat` | Runs the main chat orchestration flow. |
| `POST` | `/confirm` | Records approval or rejection for pending actions. |
| `GET` | `/memory` | Reads memory summary and history directly from `memory_store`. |
| `DELETE` | `/memory` | Deletes a session directly through `memory_store.delete_session()`. |

## Environment Variables

Loaded by `app/utils/env.py` from process env or `backend/.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `CAP Backend` | Service name returned by health routes. |
| `APP_VERSION` | `0.1.0` | Service version returned by health routes. |
| `LOG_LEVEL` | `INFO` | Logging level. |
| `DEMO_MODE` | `false` | Seeds demo data when memory initializes. |
| `CAP_DB_PATH` | `backend/data/cap.db` | SQLite database path. |
| `CORS_ORIGINS` | `http://localhost:5173`, `http://127.0.0.1:5173`, `https://cap-frontend.vercel.app` | Allowed frontend origins. |
| `GROQ_API_KEY` | None | API key for live Groq responses. |
| `GROQ_API_URL` | `https://api.groq.com/openai/v1/chat/completions` | Groq chat completions endpoint. |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model name. |
| `GROQ_TIMEOUT_SECONDS` | `8.0` | Groq request timeout. |

## Running Locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEMO_MODE=false
```

Start the backend:

```powershell
uvicorn main:app --reload --port 8000
```

Check health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Current Tool Scope

- `app/tools/executor.py` implements the first safe tool: session note saving for `save` and `write` actions.
- `update`, `organize`, and `delete` actions are acknowledged after confirmation but intentionally do not perform external side effects yet.
- Prompt templates are not loaded from `app/prompts/`; the active system prompt is loaded from `docs/ORCHESTRATION_SPEC.md`.

## Rules

- No Playwright.
- No local OS access.
- No autonomous actions without confirmation.
