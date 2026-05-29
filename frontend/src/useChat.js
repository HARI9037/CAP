import { useState, useEffect } from "react";
// Make sure this path points correctly to your api.js file
import { sendMessage, getHealth, deleteSession } from "./services/api";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatState, setChatState] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [healthStatus, setHealthStatus] = useState("unavailable");

  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem("cap_sessions");
    return saved ? JSON.parse(saved) : [];
  });

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
      const BASE_URL = import.meta.env.VITE_API_URL || "https://cap-mvp.onrender.com";
      const res = await fetch(`${BASE_URL}/memory?session_id=${id}`);
      const data = await res.json();

      if (data && Array.isArray(data.history)) {
        setMessages(data.history);
      } else if (Array.isArray(data)) {
        setMessages(data);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to recover session logs:", err);
      setMessages([]);
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
        localStorage.setItem("cap_sessions", JSON.stringify(filtered));
        return filtered;
      });

      if (sessionId === id) {
        resetSession();
      }
    } catch (err) {
      console.error("Could not clean historical record sequence:", err);
    }
  };

  const send = async (text) => {
    console.log("DEBUG: Send clicked, message:", text);
    if (!text.trim()) return;
    setLoading(true);

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await sendMessage(text, sessionId);
      console.log("DEBUG: API Response:", response);
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
          localStorage.setItem("cap_sessions", JSON.stringify(updated));
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
      console.error("DEBUG: CRITICAL ERROR in send:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setMessages([]);
  };

  return {
    messages,
    send,
    loading,
    sessionId,
    chatState,
    pendingActions,
    resetSession,
    healthStatus,
    sessions,
    loadSession,
    performDeleteSession,
  };
}
