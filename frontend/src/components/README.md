# components/
Purpose:
Reusable UI components for the CAP chat interface.
Responsibilities:
- ChatWindow — renders the conversation thread
- MessageBubble — individual message display
- ConfirmationCard — shows pending actions for user approval
- MemoryPanel — displays current session memory summary
- WarmupScreen — shown while backend cold-starts
Rules:
- No API calls inside components
- No business logic — presentational only
- Receive all data via props