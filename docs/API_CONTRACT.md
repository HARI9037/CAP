# CAP MVP API Contract (Vertical Slice 1)

Base URL:
- Set by deployment environment
- Frontend reads this from `VITE_API_URL`

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

## POST /chat
Purpose:
- Accept a user prompt and return an assistant reply.
- Creates or reuses a session in memory storage.

Request:
```json
{
  "prompt": "Continue my workflow from yesterday",
  "session_id": null
}
```

Response:
```json
{
  "ok": true,
  "session_id": "uuid-or-demo-session",
  "reply": "CAP backend is online. I received your message and the vertical slice is active.",
  "pending_actions": [],
  "memory_summary": {
    "session_id": "uuid-or-demo-session",
    "summary": "",
    "message_count": 2,
    "updated_at": "2026-01-01T00:00:00+00:00"
  }
}
```

## GET /memory
Purpose:
- Return session memory summary for the given session or latest session.

Query params:
- `session_id` (optional)

Response:
```json
{
  "ok": true,
  "memory": {
    "session_id": "uuid-or-demo-session",
    "summary": "",
    "message_count": 2,
    "updated_at": "2026-01-01T00:00:00+00:00"
  }
}
```

## POST /confirm
Purpose:
- Handle confirmation decisions.
- Confirmation is required only for mutating action types.

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
  "action_type": "write",
  "approved": true
}
```

Response (mutating):
```json
{
  "ok": true,
  "action_id": "action-123",
  "status": "approved"
}
```

Response (read-only action type):
```json
{
  "ok": true,
  "action_id": "action-123",
  "status": "not_required",
  "message": "Confirmation is not required for read-only actions."
}
```
