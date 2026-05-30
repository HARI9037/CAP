import { useState, useEffect } from "react";
// Make sure this path points correctly to your api.js file
import { sendMessage, getHealth, getMemory, deleteSession, confirmAction } from "./services/api";

function loadStoredSessions() {
  try {
    const saved = localStorage.getItem("cap_sessions");
    const parsed = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn("Ignoring invalid saved CAP sessions:", err);
    localStorage.removeItem("cap_sessions");
    return [];
  }
}

function saveStoredSessions(sessions) {
  try {
    localStorage.setItem("cap_sessions", JSON.stringify(sessions));
  } catch (err) {
    console.warn("Could not persist CAP sessions:", err);
  }
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatState, setChatState] = useState(null);
  const [sessionPhase, setSessionPhase] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [memorySummary, setMemorySummary] = useState(null);
  const [lastError, setLastError] = useState(null);
  const [lastApiResult, setLastApiResult] = useState(null);
  const [lastReply, setLastReply] = useState("");
  const [healthStatus, setHealthStatus] = useState("unavailable");

  const [sessions, setSessions] = useState(loadStoredSessions);

  // Polling engine using the backend health endpoint.
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await getHealth();
        if (data && (data.ok === true || data.status === "ready" || data.healthy === true)) {
          setHealthStatus("ready");
        } else {
          setHealthStatus("unavailable");
        }
      } catch (err) {
        setHealthStatus("unavailable");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadSession = async (id) => {
    if (!id) return;
    setSessionId(id);
    setLoading(true);
    try {
      const data = await getMemory(id);

      if (data && Array.isArray(data.history)) {
        setMessages(data.history);
      } else if (Array.isArray(data)) {
        setMessages(data);
      } else {
        setMessages([]);
      }
      const workflowState = data?.memory?.workflow_state || {};
      setMemorySummary(data?.memory || null);
      setChatState(workflowState.state || "ready");
      setSessionPhase(workflowState.phase || "general_chat");
      setPendingActions(Array.isArray(workflowState.pending_actions) ? workflowState.pending_actions : []);
      setLastError(null);
      setLastApiResult({ ok: true, label: "Memory Loaded" });
      const assistantMessages = (data?.history || []).filter((msg) => msg.role === "assistant");
      setLastReply(assistantMessages.at(-1)?.content || "");
    } catch (err) {
      console.error("Failed to recover session logs:", err);
      setMessages([]);
      setMemorySummary(null);
      setChatState(null);
      setSessionPhase(null);
      setPendingActions([]);
      setLastError("memory_load_failed");
      setLastApiResult({ ok: false, label: "Memory Error" });
    } finally {
      setLoading(false);
    }
  };

  const performDeleteSession = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await deleteSession(id);

      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== id);
        saveStoredSessions(filtered);
        return filtered;
      });

      if (sessionId === id) {
        resetSession();
      }
    } catch (err) {
      console.error("Could not clean historical record sequence:", err);
    }
  };

  const handleConfirm = async (actionId, actionType, approved) => {
    if (!sessionId) return;
    try {
      const result = await confirmAction(actionId, actionType, approved, sessionId);
      const remainingActions = Array.isArray(result.remaining_actions)
        ? result.remaining_actions
        : pendingActions.filter((action) => action.action_id !== actionId);

      setPendingActions(remainingActions);
      if (result.execution_result) {
        const execMsg = {
          role: "assistant",
          content: result.execution_result,
        };
        setMessages((prev) => [...prev, execMsg]);
      }
      if (result.memory_summary) {
        setMemorySummary(result.memory_summary);
      }
      setChatState(remainingActions.length > 0 ? "awaiting_confirmation" : "ready");
      setLastError(null);
      setLastApiResult({ ok: true, label: approved ? "Action Approved" : "Action Rejected" });
    } catch (err) {
      console.error("Confirmation failed:", err);
      setLastError("confirm_failed");
      setLastApiResult({ ok: false, label: "Confirm Failed" });
    }
  };

  const send = async (text) => {
    if (!text.trim()) return;
    setLoading(true);

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await sendMessage(text, sessionId);
      const workflowState = response.memory_summary?.workflow_state || {};
      setChatState(response.state || null);
      setSessionPhase(workflowState.phase || (response.state === "fallback" ? "fallback" : "general_chat"));
      setPendingActions(Array.isArray(response.pending_actions) ? response.pending_actions : []);
      setMemorySummary(response.memory_summary || null);
      setLastError(response.error || null);
      setLastApiResult(response.error ? { ok: false, label: response.error } : { ok: true, label: "Chat Synced" });
      setLastReply(response.reply || "");
      let currentId = sessionId;
      if (response.session_id) {
        currentId = response.session_id;
        setSessionId(response.session_id);
      }

      if (!sessionId && currentId) {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        const newSession = {
          id: currentId,
          title: text.length > 24 ? text.substring(0, 24) + "..." : text,
          time: `Today, ${timeString}`,
        };

        setSessions((prev) => {
          const updated = [newSession, ...prev];
          saveStoredSessions(updated);
          return updated;
        });
      }

      const botMsg = {
        role: "assistant",
        content: response.reply || response.error || "No response",
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      setChatState("offline");
      setSessionPhase("fallback");
      setPendingActions([]);
      setLastError("network_error");
      setLastApiResult({ ok: false, label: "Network Error" });
      const botMsg = {
        role: "assistant",
        content: "CAP could not reach the backend. Please check the API connection and try again.",
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setMessages([]);
    setChatState(null);
    setSessionPhase(null);
    setPendingActions([]);
    setMemorySummary(null);
    setLastError(null);
    setLastApiResult(null);
    setLastReply("");
  };

  return {
    messages,
    send,
    loading,
    sessionId,
    chatState,
    sessionPhase,
    pendingActions,
    memorySummary,
    lastError,
    lastApiResult,
    lastReply,
    resetSession,
    healthStatus,
    sessions,
    loadSession,
    performDeleteSession,
    handleConfirm,
  };
}
