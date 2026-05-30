# CAP MVP API Contract

Base URL:
- Frontend reads this from `VITE_API_URL`.

## GET /health
Purpose:
- Backend warmup and availability check.

Response:
```json
{
  "ok": true,
  "status": "ready",
  "service": "CAP Backend",
  "version": "0.1.0",
  "demo_mode": false
}
```

## GET /ping
Purpose:
- Lightweight health-compatible ping.

Response:
```json
{
  "ok": true,
  "status": "ok",
  "healthy": true,
  "service": "CAP Backend",
  "version": "0.1.0",
  "demo_mode": false
}
```

## POST /chat
Purpose:
- Accept a user prompt and return an assistant reply.
- Creates or reuses a session in SQLite memory.
- May return pending actions that require `/confirm`.

Request:
```json
{
  "message": "Continue my workflow from yesterday",
  "session_id": "optional-session-id"
}
```

`prompt` is also accepted as an alias for `message`.

Response:
```json
{
  "ok": true,
  "session_id": "uuid-or-demo-session",
  "reply": "Assistant response text.",
  "pending_actions": [],
  "state": "ready",
  "memory_summary": {
    "session_id": "uuid-or-demo-session",
    "summary": "Last turn - User: ... | Assistant: ...",
    "message_count": 2,
    "updated_at": "2026-01-01T00:00:00+00:00",
    "workflow_state": {
      "phase": "general_chat",
      "state": "ready",
      "pending_actions": []
    }
  },
  "error": null
}
```

## GET /memory
Purpose:
- Return session memory summary and history for the given session.
- Without `session_id`, returns the latest summary and an empty history list.

Query params:
- `session_id` optional

Response:
```json
{
  "ok": true,
  "status": "success",
  "memory": {
    "session_id": "uuid-or-demo-session",
    "summary": "",
    "message_count": 2,
    "updated_at": "2026-01-01T00:00:00+00:00",
    "workflow_state": {
      "phase": "general_chat",
      "state": "ready",
      "pending_actions": []
    }
  },
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi." }
  ]
}
```

## DELETE /memory
Purpose:
- Delete one session and its messages.

Query params:
- `session_id` required

Response:
```json
{
  "ok": true,
  "status": "success"
}
```

## POST /confirm
Purpose:
- Resolve a pending action.
- Approved `save` and `write` actions execute the session-note tool.
- Other mutating action types are acknowledged without side effects.

Mutating action types:
- `write`
- `update`
- `organize`
- `save`
- `delete`

Request:
```json
{
  "action_id": "action-123",
  "action_type": "save",
  "approved": true,
  "session_id": "uuid-or-demo-session"
}
```

Response:
```json
{
  "ok": true,
  "action_id": "action-123",
  "status": "approved",
  "execution_result": "✓ Action executed: Note 'Session Note' saved successfully.",
  "remaining_actions": [],
  "memory_summary": {
    "session_id": "uuid-or-demo-session",
    "summary": "## Session Note\n_Saved at 2026-01-01 00:00 UTC_\n\n...",
    "message_count": 2,
    "updated_at": "2026-01-01T00:00:00+00:00",
    "workflow_state": {
      "phase": "general_chat",
      "state": "ready",
      "pending_actions": []
    }
  }
}
```

Other statuses:
- `rejected`: action was rejected and removed from pending actions.
- `not_found`: action was already resolved or is no longer pending.
- `not_required`: action type is read-only and does not require confirmation.
