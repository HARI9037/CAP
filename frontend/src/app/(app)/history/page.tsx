'use client';

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useClerkApiRequest } from "@/lib/api";
import type { HistoryListResponse, HistorySessionSummary } from "@/types/chat";

function formatRelativeTime(value: string): string {
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return "Unknown";

  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  if (seconds < 60) return "Just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function sessionTitle(session: HistorySessionSummary): string {
  return session.summary?.trim() || "Untitled conversation";
}

export default function HistoryPage() {
  const apiRequest = useClerkApiRequest();
  const [sessions, setSessions] = useState<HistorySessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      setLoading(true);
      setError(null);

      try {
        const result = await apiRequest<HistoryListResponse>("/history");
        if (!active) return;
        setSessions(Array.isArray(result.conversations) ? result.conversations : []);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unknown error");
        setSessions([]);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="flex-1 p-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Conversation archive
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">History</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Reopen a previous chat and continue it against the same backend session.
            </p>
          </div>
          <Button asChild>
            <Link href="/chat">New chat</Link>
          </Button>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        ) : null}

        <Card className="border-border bg-card/80 shadow-sm">
          <CardContent className="p-4">
            {loading ? (
              <div className="rounded-md border border-dashed border-border bg-background/60 px-4 py-10 text-center text-sm text-muted-foreground">
                Loading conversations...
              </div>
            ) : sessions.length === 0 ? (
              <div className="rounded-md border border-dashed border-border bg-background/60 px-4 py-10 text-center text-sm text-muted-foreground">
                No conversations yet
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <Link
                    key={session.session_id}
                    href={`/chat?session=${encodeURIComponent(session.session_id)}`}
                    className="group flex items-center justify-between gap-4 rounded-md border border-border bg-background p-4 transition-colors hover:bg-muted"
                  >
                    <div className="min-w-0 space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <History className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="truncate">{sessionTitle(session)}</span>
                      </div>
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        <span>{formatRelativeTime(session.updated_at)}</span>
                        <span>{session.message_count} message{session.message_count === 1 ? "" : "s"}</span>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1" />
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
