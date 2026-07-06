"use client";

import { useEffect, useState } from "react";
import { Database, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useClerkApiRequest } from "@/lib/api";

type MemoryItem = {
  memory_id: string;
  memory_type: string;
  title: string;
  content: string;
  source_session_id: string | null;
  created_at: string;
  updated_at: string;
};

type MemoryItemsResponse = {
  ok: boolean;
  memories: MemoryItem[];
};

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export default function MemoryPage() {
  const apiRequest = useClerkApiRequest();
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadMemories() {
      setLoading(true);
      setError(null);

      try {
        const result = await apiRequest<MemoryItemsResponse>("/memory/items");
        if (!active) return;
        setMemories(Array.isArray(result.memories) ? result.memories : []);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unknown error");
        setMemories([]);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadMemories();

    return () => {
      active = false;
    };
  }, []);

  async function deleteMemory(memoryId: string) {
    const previous = memories;
    setDeletingId(memoryId);
    setError(null);
    setMemories((current) => current.filter((memory) => memory.memory_id !== memoryId));

    try {
      await apiRequest(`/memory/items/${encodeURIComponent(memoryId)}`, { method: "DELETE" });
    } catch (err) {
      setMemories(previous);
      setError(err instanceof Error ? err.message : "Could not delete memory");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="flex-1 p-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="border-b border-border pb-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Stored context
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">Memory</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Review and remove the facts, goals, preferences, and project context CAP can reuse.
          </p>
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
                Loading memory...
              </div>
            ) : memories.length === 0 ? (
              <div className="rounded-md border border-dashed border-border bg-background/60 px-4 py-10 text-center text-sm text-muted-foreground">
                No stored memory yet
              </div>
            ) : (
              <div className="space-y-3">
                {memories.map((memory) => (
                  <div key={memory.memory_id} className="rounded-md border border-border bg-background p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="min-w-0 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center gap-2 text-sm font-medium">
                            <Database className="h-4 w-4 text-muted-foreground" />
                            {memory.title}
                          </span>
                          <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                            {memory.memory_type}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{memory.content}</p>
                        <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                          <span>Updated {formatDate(memory.updated_at)}</span>
                          {memory.source_session_id ? <span>Source {memory.source_session_id.slice(0, 8)}...</span> : null}
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => deleteMemory(memory.memory_id)}
                        disabled={deletingId === memory.memory_id}
                        aria-label={`Delete ${memory.title}`}
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
