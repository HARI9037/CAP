import { useState } from "react";
import { sendMessage } from "../services/api";

export function useChat() {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);

    const send = async (text) => {
        setLoading(true);

        const userMsg = { role: "user", content: text };
        setMessages((prev) => [...prev, userMsg]);

        const response = await sendMessage(text, sessionId);

        if (response.session_id) {
            setSessionId(response.session_id);
        }

        const botMsg = {
            role: "assistant",
            content: response.reply || response.error || "No response",
        };

        setMessages((prev) => [...prev, botMsg]);

        setLoading(false);
    };

    return {
        messages,
        send,
        loading,
        sessionId,
    };
}