import { useState, useEffect } from "react";
import { sendMessage, getHealth } from "./services/api";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatState, setChatState] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [healthStatus, setHealthStatus] = useState("loading");

  // 1. Properly handles backend health checking with an exact string state match
  useEffect(() => {
    getHealth()
      .then((res) => {
        if (res && res.status === "ready") {
          setHealthStatus("ready");
        } else {
          setHealthStatus("error");
        }
      })
      .catch(() => setHealthStatus("error"));
  }, []);

  const send = async (text) => {
    if (!text.trim()) return;

    setLoading(true);

    // Optimistically update UI with user message immediately
    const userMsg = { role: "user", content: text };
    setMessages((p) => [...p, userMsg]);

    // 2. The Critical Safety Net: Robust Try-Catch Block
    try {
      const resp = await sendMessage(text, sessionId);

      // Prevent undefined object runtime crashes if the network drops or server delays
      if (resp) {
        if (resp.session_id) setSessionId(resp.session_id);

        setChatState(resp.state || null);
        setPendingActions(Array.isArray(resp.pending_actions) ? resp.pending_actions : []);

        // Safely map dynamic assistant field variations from backend route layers
        const botMsg = {
          role: "assistant",
          content: resp.reply || resp.response || "No response content received."
        };
        setMessages((p) => [...p, botMsg]);
      } else {
        throw new Error("Empty response object received from backend infrastructure");
      }

    } catch (error) {
      console.error("CAP Integration Boundary Error:", error);

      // Fallback message to prevent frontend UI freezes during Render Cold Starts
      const errorMsg = {
        role: "assistant",
        content: "🚨 Connection to CAP timed out! The backend server might be waking up from a sleep cycle (Render Cold Start). Please wait a moment and try again."
      };
      setMessages((p) => [...p, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setMessages([]);
    setChatState(null);
    setPendingActions([]);
  };

  return {
    messages,
    send,
    loading,
    sessionId,
    chatState,
    pendingActions,
    resetSession,
    healthStatus
  };
}