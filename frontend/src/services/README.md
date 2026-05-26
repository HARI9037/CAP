# services/
Purpose:
All HTTP communication between frontend and backend API.
Responsibilities:
- sendMessage(prompt) — POST /chat
- getMemory() — GET /memory
- confirmAction(actionId) — POST /confirm
- checkHealth() — GET /health
Rules:
- All API calls go through this folder only
- Use VITE_API_URL for base URL
- Handle errors gracefully and return structured responses