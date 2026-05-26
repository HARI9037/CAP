# orchestrator/
Purpose:
Handles all Groq API communication and workflow reasoning.
Responsibilities:
- Send user prompt to Groq API with system context
- Receive retrieved context from memory BEFORE planning
- Parse LLM response and decide which tools to invoke
- Plan multi-step workflow execution
- Dispatch tool calls to tool manager
Rules:
- No direct database access
- No UI logic
- No tool execution — orchestrator decides, tools execute