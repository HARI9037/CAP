import { useState } from "react";
import { useChat } from "./useChat";

function Badge({ state }) {
  const colors = {
    ready: "#28a745",
    awaiting_confirmation: "#ffb400",
    fallback: "#dc3545",
    error: "#c82333",
  };
  const color = colors[state] || "#6c757d";
  return (
    <span
      style={{
        backgroundColor: color,
        color: "#fff",
        borderRadius: "12px",
        padding: "2px 8px",
        fontSize: "0.85rem",
        marginLeft: "8px",
        textTransform: "capitalize",
      }}
    >
      {state.replace("_", " ")}
    </span>
  );
}

export default function App() {
  const [input, setInput] = useState("");
  const {
    messages,
    send,
    loading,
    chatState,
    pendingActions,
    sessionId,
    resetSession,
    healthStatus,
  } = useChat();

  const handleSend = () => {
    if (!input.trim()) return;
    send(input);
    setInput("");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0f1117",
        color: "#f5f7fa",
        fontFamily: "'Inter', sans-serif",
        display: "flex",
        justifyContent: "center",
        paddingTop: "2rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "600px",
          backgroundColor: "#1a1d26",
          borderRadius: "8px",
          padding: "20px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "12px",
            flexWrap: "wrap",
          }}
        >
          <h2 style={{ margin: 0 }}>CAP Chat</h2>
          {chatState && <Badge state={chatState} />}
          {sessionId && (
            <span style={{ marginLeft: "8px", fontSize: "0.85rem", opacity: 0.8 }}>
              Memory Active
            </span>
          )}
          <button
            onClick={resetSession}
            style={{
              marginLeft: "auto",
              padding: "4px 8px",
              background: "#0066ff",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            New Session
          </button>
        </div>

        {/* Health banner */}
        {healthStatus === "loading" && (
          <div
            style={{
              background: "#ffeb3b",
              color: "#000",
              padding: "8px",
              borderRadius: "4px",
              marginBottom: "12px",
            }}
          >
            Connecting to CAP backend…
          </div>
        )}
        {healthStatus === "ready" && (
          <div
            style={{
              background: "#28a745",
              color: "#fff",
              padding: "8px",
              borderRadius: "4px",
              marginBottom: "12px",
            }}
          >
            Backend Ready
          </div>
        )}
        {healthStatus === "error" && (
          <div
            style={{
              background: "#dc3545",
              color: "#fff",
              padding: "8px",
              borderRadius: "4px",
              marginBottom: "12px",
            }}
          >
            Backend unavailable – please check the server.
          </div>
        )}

        {/* Pending actions */}
        {Array.isArray(pendingActions) && pendingActions.length > 0 && (
          <div style={{ marginBottom: "12px" }}>
            <strong>Pending Actions:</strong>
            <div style={{ marginTop: "8px" }}>
              {pendingActions.map((a, i) => (
                <div
                  key={i}
                  style={{
                    background: "#232838",
                    borderRadius: "6px",
                    padding: "8px",
                    marginBottom: "8px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  <span style={{ marginRight: "8px" }}>⚙️</span>
                  <div>
                    <div style={{ fontWeight: "600" }}>{a.action_type}</div>
                    <div style={{ fontSize: "0.85rem", opacity: 0.8 }}>
                      {a.description || a.payload?.description || "(no description)"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chat messages */}
        <div
          style={{
            minHeight: "200px",
            marginBottom: "12px",
            overflowY: "auto",
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                marginBottom: "8px",
              }}
            >
              <div
                style={{
                  maxWidth: "80%",
                  backgroundColor: m.role === "assistant" ? "#232838" : "#2d4cff",
                  color: "#f5f7fa",
                  borderRadius: "12px",
                  padding: "8px 12px",
                }}
              >
                <strong>{m.role}:</strong> {m.content}
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div style={{ display: "flex", alignItems: "center" }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type message..."
            disabled={loading}
            style={{
              flexGrow: 1,
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #444",
              background: "#0f1117",
              color: "#f5f7fa",
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading}
            style={{
              marginLeft: "8px",
              padding: "8px 16px",
              background: "#0066ff",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "default" : "pointer",
            }}
          >
            {loading ? "CAP is thinking…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
