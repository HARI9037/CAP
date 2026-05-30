# memory/

## Purpose

SQLite-backed session memory for CAP.
The memory layer stores conversation history, workflow state, pending actions, and short session summaries.

## Responsibilities

- Initialize the SQLite database.
- Create or reuse sessions.
- Append user and assistant messages.
- Read ordered session history.
- Read and update workflow state.
- Store pending actions.
- Store short session summaries.
- Delete sessions and their messages.
- Seed `demo-session-001` when `demo_mode=True` and the database is empty.

## Schema

`sessions`

- `session_id` - `TEXT PRIMARY KEY`
- `summary` - `TEXT`
- `workflow_state` - JSON blob stored as `TEXT`
- `created_at` - timestamp string
- `updated_at` - timestamp string

`messages`

- `message_id` - `TEXT PRIMARY KEY`
- `id` - `INTEGER` ordering column
- `session_id` - session foreign key
- `role` - message role
- `content` - message text
- `timestamp` - timestamp string

## Key Methods

- `initialize(db_path, demo_mode=False)`
- `ensure_session(session_id=None)`
- `append_message(session_id, role, content)`
- `get_session_history(session_id)`
- `get_session_phase(session_id)`
- `store_pending_actions(session_id, actions)`
- `update_session_workflow_state(session_id, updates)`
- `update_session_summary(session_id, summary)`
- `get_session_summary(session_id=None)`
- `delete_session(session_id)`

## Stored Data

- Conversation history.
- Workflow state.
- Pending actions.
- Session summary.

Not stored here:

- Research references.
- User preferences.
- Per-session files.
- Log files.

## Rules

- No UI logic.
- No tool execution.
- No Groq API calls.
- Writes are protected with `threading.Lock`.
