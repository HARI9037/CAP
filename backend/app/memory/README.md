# memory/
Purpose:
Stores workflow continuity and handles contextual retrieval.
Responsibilities:
- SQLite database management
- Save session history and workflow state
- Retrieve previous context for orchestrator
- Seed demo workflows on startup if database is empty
Stored Data:
- conversation history
- workflow state
- session summaries
- research references
- user preferences
Rules:
- No UI logic
- No tool execution
- On startup: if database empty, insert demo workflow data
  so the memory demo always works for judges