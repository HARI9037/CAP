# CAP Orchestration Execution Specification

This document defines the strict execution specification for the CAP (Context-Aware Partner) orchestration brain. It is designed to be directly implemented by a backend developer to integrate the Groq API for a stable, 2-minute hackathon demonstration.

## 1. System Roles
- **CAP Orchestrator**: The central controller. Responsible for receiving user input, maintaining session context, querying the Groq LLM, parsing the structured response, and determining if human-in-the-loop confirmation is required before proceeding.
- **Groq LLM**: The reasoning engine. Responsible ONLY for generating user-facing replies and proposing structured actions. It does NOT execute actions directly.
- **Action Executor**: A module that runs the tool logic ONLY after user confirmation is received via the `/confirm` endpoint.

## 2. Execution Phases
The orchestrator must track the current workflow state in `MemoryStore` and inject it into the prompt.
1. **`architecture_review` (Demo Phase)**: The system expects discussions around cloud infrastructure, load balancers, and security groups. It is biased towards proposing diagram updates or configuration changes.
2. **`general_chat`**: Standard conversational mode for general inquiries where no specific workflow context is active.
3. **`fallback`**: A designated safe state triggered during API timeouts or parsing errors, designed to prevent the demo from crashing.

## 3. Decision Rules
- **When to call the LLM**: 
  - On every new `POST /chat` request from the user.
  - After a tool is successfully executed (to generate a summary of the result).
- **When to respond directly (Skip LLM)**: 
  - If a user sends a `/confirm` request for a rejected action, immediately return an aborted status to the UI without querying the LLM.
- **When to use fallback response**:
  - If the Groq API times out (> 8 seconds).
  - If the Groq API returns a 500 error.
  - If the LLM response cannot be successfully parsed as valid JSON matching the Output Schema.

## 4. Tool Contract
Although tools are currently empty, the interface must strictly follow this contract to allow future implementation.
**Input payload from LLM to Backend**:
```json
{
  "action_id": "uuid-v4",
  "action_type": "write | update | organize | save | delete",
  "description": "Human readable description of what the tool will do (shown in UI)",
  "payload": {
    "target_resource": "string",
    "parameters": {}
  }
}
```
**Output payload from Backend to LLM (post-execution)**:
```json
{
  "success": true,
  "message": "Tool executed successfully",
  "data": {}
}
```

## 5. System Prompt
The following prompt MUST be injected into every Groq API request as the `system` role message:

```text
You are CAP (Context-Aware Partner), an AI workflow assistant.
Your core philosophy is: THINK IN CLOUD -> ANSWER CLEARLY -> CONFIRM REAL STATE CHANGES.

Current Workflow Phase: {current_phase}

You must ALWAYS respond in valid JSON matching exactly this schema:
{
  "reply": "Your conversational response to the user.",
  "pending_actions": [
    {
      "action_id": "unique-string",
      "action_type": "update",
      "description": "What this action will do",
      "payload": {}
    }
  ]
}

Rules:
1. CRITICAL: Return ONLY a raw JSON object. No markdown. No ```json fences. No prose before or after. Your entire response must start with { and end with }.
2. If the user asks for informational content in chat, such as a roadmap, workflow, checklist, plan, guide, explanation, comparison, feature list, recommendation, or tech stack, put the complete useful answer in "reply" and return [] for "pending_actions".
3. Only propose a pending action when the user explicitly asks you to save, remember, modify an existing stored item, update a resource, organize stored material, delete something, or perform another state-changing operation outside the visible chat answer.
4. Do NOT create pending actions for normal advice, planning, brainstorming, recommendations, learning help, app-building guidance, feature suggestions, or tech-stack suggestions.
5. For roadmap, workflow, checklist, plan, feature, and tech-stack requests, include concrete steps, day-by-day or section-by-section detail, and enough substance to be directly useful. Do not answer with only a title or heading.
6. Keep your conversational style professional, but do not shorten requested content when the user asks for detail.
7. If no actions are required, return an empty array [] for "pending_actions".
8. NEVER explain yourself outside the JSON. NEVER say "Here is the JSON". Just output the JSON.
```

## 6. Output Format Schema
The backend must parse the Groq LLM string response using `json.loads()` and validate it against this Pydantic schema:

```python
from pydantic import BaseModel, Field

class PendingAction(BaseModel):
    action_id: str
    action_type: str
    description: str
    payload: dict

class LLMResponse(BaseModel):
    reply: str
    pending_actions: list[PendingAction] = Field(default_factory=list)
```

## 7. Failure Handling Rules
To ensure a flawless 2-minute judge demo, the system MUST NOT crash under any circumstances. Implement the following `try/except` block logic in `service.py`:

- **Groq API Timeout (`httpx.TimeoutException`)**:
  - Catch the error and immediately return a structured `ChatResult`.
  - Reply: `"I'm experiencing a slight network delay on the backend. Could you try sending that again?"`
- **JSON Parsing Failure (`json.JSONDecodeError` or `ValidationError`)**:
  - Catch the error.
  - Reply: `"I processed your request, but hit a minor formatting glitch. Let's continue our architecture review—what would you like to check next?"`
  - Ensure `pending_actions` is forced to `[]`.
- **Tool Execution Failure**:
  - If a confirmed tool fails, return a safe error directly to the frontend.
  - Reply: `"The requested action could not be completed at this time, but our session context is saved."`
