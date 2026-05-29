import { useState, useEffect } from "react";
import { sendMessage, getHealth } from "./services/api";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatState, setChatState] = useState(null);
  const [pendingActions, setPendingActions] = useState([]);
  const [healthStatus, setHealthStatus] = useState("unavailable");

  // Read initialized sessions straight out of localStorage on boot
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem("cap_sessions");
    return saved ? JSON.parse(saved) : [];
  });

  // PRIORITY 2 FIX: Real-time active health checking against backend
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await getHealth();
        if (data) {
          setHealthStatus("ready");
        } else {
          setHealthStatus("unavailable");
        }
      } catch (err) {
        setHealthStatus("unavailable");
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000); // Poll engine status every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // PRIORITY 1 FIX: Retrieve explicit message history context from memory endpoint
  const loadSession = async (id) => {
    if (!id) return;
    setSessionId(id);
    setLoading(true);
    try {
      const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${BASE_URL}/memory?session_id=${id}`);
      const data = await res.json();

      if (Array.isArray(data)) {
        setMessages(data);
      } else if (data && Array.isArray(data.messages)) {
        setMessages(data.messages);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to recover session log framework:", err);
    } finally {
      setLoading(false);
    }
  };

  const send = async (text) => {
    if (!text.trim()) return;
    setLoading(true);

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await sendMessage(text, sessionId);

      let currentId = sessionId;
      if (response.session_id) {
        currentId = response.session_id;
        setSessionId(response.session_id);
      }

      // PRIORITY 1 FIX: If this is the initial interaction string, record manifest data
      if (!sessionId && currentId) {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        const formattedTime = `Today, ${timeString}`;

        const newSession = {
          id: currentId,
          title: text.length > 28 ? text.substring(0, 28) + "..." : text,
          time: formattedTime,
        };

        setSessions((prev) => {
          const updated = [newSession, ...prev];
          localStorage.setItem("cap_sessions", JSON.stringify(updated));
          return updated;
        });
      }

      if (response.state) {
        setChatState(response.state);
      } else {
        setChatState(null);
      }

      if (Array.isArray(response.pending_actions)) {
        setPendingActions(response.pending_actions);
      } else {
        setPendingActions([]);
      }

      const botMsg = {
        role: "assistant",
        content: response.reply || response.error || "No response",
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Error during dispatch execution loop:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Terminated handshake connection with backend." },
      ]);
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
    chatState,
    pendingActions,
    sessionId,
    resetSession,
    healthStatus,
    sessions,
    loadSession,
  };
}