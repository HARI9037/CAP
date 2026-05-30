# orchestrator/

## Purpose

Core orchestration layer for CAP chat requests.
It connects session memory, the runtime system prompt, the Groq API call, response parsing, pending action state, and fallback handling.

## Responsibilities

- Receive chat messages from the `/chat` route.
- Create or reuse a session through `memory_store`.
- Store user and assistant messages.
- Load the current phase and session history.
- Load the system prompt from `docs/ORCHESTRATION_SPEC.md`.
- Call the Groq API through synchronous `httpx.Client`.
- Require JSON object responses with `reply` and `pending_actions`.
- Parse defensive JSON output, including fenced blocks, partial JSON, and reply aliases.
- Store pending actions in SQLite.
- Set workflow state to `ready`, `awaiting_confirmation`, or `fallback`.
- Handle confirmation decisions through `handle_confirmation()`.
- Return safe fallback replies for timeouts, HTTP errors, JSON parse errors, and validation errors.

## Core Flow

`process_chat_message(message, session_id, settings)`:

1. Require settings.
2. Ensure an active session.
3. Append the user message.
4. Read the current session phase.
5. Read session history.
6. Call Groq with the system prompt and session history.
7. Parse the model response into `LLMResponse`.
8. Append the assistant reply.
9. Store pending actions and set state to `awaiting_confirmation`, if actions exist.
10. Clear pending actions and set state to `ready`, if no actions exist.
11. Update the session summary.
12. Return `ChatResult`.

Fallback flow:

- Missing Groq key returns `groq_configuration_missing`.
- Groq timeout returns `groq_timeout`.
- Groq HTTP or request failures return `groq_api_failure`.
- Invalid model output returns `llm_parse_failure`.

## Rules

- DOES call `memory_store` directly.
- Does NOT dispatch to a tool manager; tools are not implemented.
- Does NOT do multi-step planning; each `/chat` request is handled as one turn.
- No UI logic.
