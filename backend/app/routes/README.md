# routes/
Purpose:
FastAPI route definitions for all frontend-backend communication.
Endpoints:
- POST /chat — receive user prompt, return AI response
- GET /health — backend warmup and availability check
- POST /confirm — receive user approval for pending actions
- GET /memory — return current session memory summary
Rules:
- REST API only
- No business logic inside routes
- Delegate everything to orchestrator
- Keep routes thin