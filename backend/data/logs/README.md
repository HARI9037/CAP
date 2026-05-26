# logs/
Purpose:
Stores runtime logs for debugging and monitoring.
Responsibilities:
- API request logs
- Tool execution logs
- Error logs
Rules:
- Write-only during runtime
- Never read by orchestrator or tools
- For debugging purposes only