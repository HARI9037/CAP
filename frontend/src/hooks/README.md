# hooks/
Purpose:
Custom React hooks for shared stateful logic.
Responsibilities:
- useChat — manages conversation state and API communication
- useMemory — fetches and displays session memory
- useConfirmation — handles pending action approval flow
- useHealthCheck — pings backend on load, triggers warmup screen
Rules:
- No UI rendering inside hooks
- Hooks must be reusable and single-purpose