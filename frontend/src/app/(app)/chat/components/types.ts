export interface PendingAction {
  action_id: string;
  action_type: string;
  description: string;
  payload: Record<string, unknown>;
}

export interface WorkflowState {
  phase?: string;
  state?: string;
  pending_actions?: PendingAction[];
  [key: string]: unknown;
}

export interface MemorySummary {
  summary?: string;
  message_count?: number;
  session_id?: string;
  workflow_state?: WorkflowState;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}
