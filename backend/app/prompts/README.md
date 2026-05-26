# prompts/
Purpose:
All system prompts and prompt templates used by the orchestrator.
Responsibilities:
- CAP system prompt — defines agent identity and behavior
- Workflow continuation prompt template
- Tool decision prompt template
- Confirmation summary prompt template
Rules:
- No Python logic in this folder
- Plain text or Python string constants only
- Every prompt must reinforce:
  THINK IN CLOUD → ACT LOCALLY → CONFIRM EVERYTHING