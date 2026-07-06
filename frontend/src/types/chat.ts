import type { PendingAction } from "@/app/(app)/chat/components/types";

export type ChatResponse = {
  ok: boolean;
  session_id: string;
  reply: string;
  pending_actions: any[];
  state: string;
  memory_summary?: any;
  error?: any;
};

export type ConfirmResponse = {
  ok?: boolean;
  remaining_actions?: PendingAction[];
  memory_summary?: any;
  execution_result?: string;
  error?: any;
};

export type HistorySessionSummary = {
  session_id: string;
  summary: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type HistoryListResponse = {
  ok: boolean;
  conversations: HistorySessionSummary[];
};

export type HistoryMessage = {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type HistoryDetailResponse = {
  ok: boolean;
  session_id: string;
  messages: HistoryMessage[];
  memory?: any;
};
