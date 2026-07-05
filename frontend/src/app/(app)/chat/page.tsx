'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useClerkApiRequest } from '@/lib/api';
import type { ChatResponse, ConfirmResponse } from '@/types/chat';

import { ChatInput } from "./components/chat-input";
import { ChatMessages } from "./components/chat-messages";
import { MemorySummaryPanel } from "./components/memory-summary-panel";
import type { ChatMessage, MemorySummary, PendingAction } from "./components/types";

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
  };
}

export default function ChatPage() {
  const apiRequest = useClerkApiRequest();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [reply, setReply] = useState('');
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [memorySummary, setMemorySummary] = useState<MemorySummary | null>(null);
  const [chatState, setChatState] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, pendingActions, loading, reply]);

  const sessionLabel = useMemo(() => {
    return sessionId ? `${sessionId.slice(0, 8)}...` : "new session";
  }, [sessionId]);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setError(null);
    setReply("");
    setPendingActions([]);

    const userMessage = createMessage("user", message.trim());
    setMessages((current) => [...current, userMessage]);

    try {
      const result = await apiRequest<ChatResponse>('/chat', {
        method: 'POST',
        body: JSON.stringify({ message: message.trim(), session_id: sessionId }),
      });

      const nextReply = typeof result?.reply === "string" ? result.reply : "";
      const nextPendingActions = Array.isArray(result?.pending_actions) ? result.pending_actions : [];

      setReply(nextReply);
      setPendingActions(nextPendingActions);
      setMemorySummary(result?.memory_summary ?? null);
      setChatState(result?.state ?? null);
      if (result?.session_id) {
        setSessionId(result.session_id);
      }

      setMessages((current) => [
        ...current,
        createMessage("assistant", nextReply || "No response"),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setMessages((current) => [
        ...current,
        createMessage("assistant", "CAP could not reach the backend. Please try again."),
      ]);
    } finally {
      setLoading(false);
      setMessage('');
    }
  };

  const handleActionDecision = async (action: PendingAction, approved: boolean) => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await apiRequest<ConfirmResponse>('/confirm', {
        method: 'POST',
        body: JSON.stringify({
          action_id: action.action_id,
          action_type: action.action_type,
          approved,
          session_id: sessionId,
        }),
      });

      const remainingActions = Array.isArray(result?.remaining_actions)
        ? result.remaining_actions
        : pendingActions.filter((currentAction) => currentAction.action_id !== action.action_id);

      setPendingActions(remainingActions);
      setMemorySummary(result?.memory_summary ?? memorySummary);
      setChatState(remainingActions.length > 0 ? "awaiting_confirmation" : "ready");

      const executionResult = result?.execution_result;
      if (typeof executionResult === "string" && executionResult.trim()) {
        setMessages((current) => [...current, createMessage("assistant", executionResult)]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-5xl flex-col gap-6 px-4 py-6 md:px-6">
      <div className="flex flex-col gap-2 border-b border-border pb-4">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
          Authenticated chat
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">Chat</h1>
          <span className="rounded-full border border-border bg-muted px-3 py-1 text-xs text-muted-foreground">
            {sessionLabel}
          </span>
        </div>
      </div>

      <MemorySummaryPanel memorySummary={memorySummary} sessionId={sessionId} chatState={chatState} />

      {error ? (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
          <strong className="font-semibold">Error:</strong> {error}
        </div>
      ) : null}

      <div className="flex-1 space-y-6">
        <ChatMessages
          messages={messages}
          pendingActions={pendingActions}
          loading={loading}
          onApproveAction={(action) => handleActionDecision(action, true)}
          onRejectAction={(action) => handleActionDecision(action, false)}
        />
        <div ref={scrollAnchorRef} />
      </div>

      <ChatInput value={message} onChange={setMessage} onSubmit={handleSendMessage} loading={loading} />
    </div>
  );
}
