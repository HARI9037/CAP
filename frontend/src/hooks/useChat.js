import { useMemo, useState } from "react";

import { sendMessage } from "../services/api";

function buildMessage(role, content) {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: new Date().toISOString(),
  };
}

export default function useChat() {
  const [messages, setMessages] = useState([
    buildMessage(
      "assistant",
      "CAP is ready. Ask me to continue your workflow.",
    ),
  ]);
  const [sessionId, setSessionId] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [isSending, setIsSending] = useState(false);

  const canSend = useMemo(() => !isSending, [isSending]);

  const sendPrompt = async (prompt) => {
    if (!canSend) {
      return { ok: false, message: "A request is already in progress." };
    }
    setIsSending(true);
    setMessages((current) => [...current, buildMessage("user", prompt)]);

    const response = await sendMessage(prompt, sessionId);
    if (!response.ok) {
      setMessages((current) => [
        ...current,
        buildMessage("assistant", `Request failed: ${response.message}`),
      ]);
      setIsSending(false);
      return response;
    }

    const payload = response.data;
    setSessionId(payload.session_id ?? null);
    setPendingActions(Array.isArray(payload.pending_actions) ? payload.pending_actions : []);
    setMessages((current) => [
      ...current,
      buildMessage("assistant", payload.reply ?? "CAP backend responded."),
    ]);
    setIsSending(false);
    return response;
  };

  return {
    messages,
    sessionId,
    pendingActions,
    isSending,
    sendPrompt,
  };
}
