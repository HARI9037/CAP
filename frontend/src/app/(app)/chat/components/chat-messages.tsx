import { ChatMessage } from "./chat-message";
import { PendingActions } from "./pending-actions";
import { TypingIndicator } from "./typing-indicator";
import type { ChatMessage as ChatMessageType, PendingAction } from "./types";

interface ChatMessagesProps {
  messages: ChatMessageType[];
  pendingActions: PendingAction[];
  loading?: boolean;
  onApproveAction: (action: PendingAction) => void;
  onRejectAction: (action: PendingAction) => void;
}

export function ChatMessages({
  messages,
  pendingActions,
  loading = false,
  onApproveAction,
  onRejectAction,
}: ChatMessagesProps) {
  const lastAssistantIndex = [...messages].reverse().findIndex((message) => message.role === "assistant");
  const assistantInsertIndex = lastAssistantIndex === -1 ? -1 : messages.length - 1 - lastAssistantIndex;

  return (
    <div className="space-y-4 rounded-2xl border border-border bg-card/60 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-border pb-3">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Conversation
          </div>
          <div className="mt-1 text-sm font-medium text-foreground">Chat stream</div>
        </div>
        <div className="text-xs text-muted-foreground">
          {messages.length} {messages.length === 1 ? "message" : "messages"}
        </div>
      </div>

      <div className="space-y-4">
        {messages.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-background/60 px-4 py-8 text-center text-sm text-muted-foreground">
            Start the conversation by sending a message.
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={message.id} className="space-y-4">
              <ChatMessage message={message} />
              {index === assistantInsertIndex && pendingActions.length > 0 ? (
                <PendingActions
                  actions={pendingActions}
                  onApprove={onApproveAction}
                  onReject={onRejectAction}
                  disabled={loading}
                />
              ) : null}
            </div>
          ))
        )}

        {loading ? <TypingIndicator /> : null}
      </div>
    </div>
  );
}
