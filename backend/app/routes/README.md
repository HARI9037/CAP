# routes/

## Purpose

Thin FastAPI route handlers for CAP backend endpoints.

## Endpoints

| Method | Path | Delegates to | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | `get_health_status()` | Returns backend readiness, service name, version, and demo mode. |
| `GET` | `/ping` | `get_health_status()` | Compatibility health endpoint with `healthy: true`. |
| `POST` | `/chat` | `process_chat_message()` | Validates chat input and runs the orchestrator flow. |
| `POST` | `/confirm` | `handle_confirmation()` | Records approval or rejection for a pending action. |
| `GET` | `/memory` | `memory_store` directly | Returns memory summary and history for a session. |
| `DELETE` | `/memory` | `memory_store.delete_session()` directly | Deletes a session and its messages. |

## Rules

- Routes stay thin.
- No business logic in route handlers.
- REST endpoints only.
- Memory routes call `memory_store` directly, not the orchestrator.
