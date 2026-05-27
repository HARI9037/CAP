import { useState, useEffect } from "react";
import { sendMessage, getHealth } from "./services/api";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatState, setChatState] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [healthStatus, setHealthStatus] = useState("loading");

  useEffect(() => {
    getHealth()
      .then((res) => setHealthStatus(res.status === "ok" ? "ready" : "error"))
      .catch(() => setHealthStatus("error"));
  }, []);

  const send = async (text) => {
    setLoading(true);
    const userMsg = { role: "user", content: text };
    setMessages((p) => [...p, userMsg]);
    const resp = await sendMessage(text, sessionId);
    if (resp.session_id) setSessionId(resp.session_id);
    setChatState(resp.state || null);
    setPendingActions(Array.isArray(resp.pending_actions) ? resp.pending_actions : []);
    const botMsg = { role: "assistant", content: resp.reply || resp.error || "No response" };
    setMessages((p) => [...p, botMsg]);
    setLoading(false);
  };

  const resetSession = () => {
    setSessionId(null);
    setMessages([]);
    setChatState(null);
    setPendingActions([]);
  };

  return { messages, send, loading, sessionId, chatState, pendingActions, healthStatus, resetSession };
}
