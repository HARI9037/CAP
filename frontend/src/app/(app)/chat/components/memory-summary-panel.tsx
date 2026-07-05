import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { MemorySummary } from "./types";

interface MemorySummaryPanelProps {
  memorySummary: MemorySummary | null;
  sessionId: string | null;
  chatState: string | null;
}

export function MemorySummaryPanel({ memorySummary, sessionId, chatState }: MemorySummaryPanelProps) {
  const summary = memorySummary?.summary?.trim() || "Session memory will appear after CAP responds.";
  const messageCount = memorySummary?.message_count ?? 0;
  const workflowState = memorySummary?.workflow_state;
  const phase = workflowState?.phase || chatState || "general_chat";
  const sessionLabel = sessionId ? `${sessionId.slice(0, 8)}...` : "none";

  return (
    <Card className="border-border bg-card/80 shadow-sm">
      <CardHeader className="space-y-3 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-sm uppercase tracking-[0.18em] text-muted-foreground">
            Session Summary
          </CardTitle>
          <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            {chatState || "ready"}
          </span>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <div className="rounded-md border border-border bg-background px-3 py-2">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Session
            </div>
            <div className="mt-1 truncate text-sm font-medium text-foreground">
              {sessionLabel}
            </div>
          </div>
          <div className="rounded-md border border-border bg-background px-3 py-2">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Phase
            </div>
            <div className="mt-1 truncate text-sm font-medium text-foreground">
              {phase}
            </div>
          </div>
          <div className="rounded-md border border-border bg-background px-3 py-2">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Messages
            </div>
            <div className="mt-1 truncate text-sm font-medium text-foreground">
              {messageCount}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm leading-6 text-muted-foreground">
          {summary}
        </p>
      </CardContent>
    </Card>
  );
}
