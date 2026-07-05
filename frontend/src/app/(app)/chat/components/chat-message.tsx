import { cn } from "@/lib/utils";

import type { ChatMessage as ChatMessageType } from "./types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[min(42rem,92%)] rounded-2xl border px-4 py-3 shadow-sm",
          isUser
            ? "border-primary/30 bg-primary text-primary-foreground"
            : "border-border bg-card text-card-foreground"
        )}
      >
        <div
          className={cn(
            "mb-2 flex items-center justify-between gap-3 text-[10px] font-semibold uppercase tracking-[0.18em]",
            isUser ? "text-primary-foreground/80" : "text-muted-foreground"
          )}
        >
          <span>{isUser ? "You" : "CAP"}</span>
        </div>
        <div className="whitespace-pre-wrap break-words text-sm leading-6">
          {message.content}
        </div>
      </div>
    </div>
  );
}
