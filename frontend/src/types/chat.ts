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
