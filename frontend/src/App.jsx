import { useState } from "react";
import { useChat } from "./useChat";

/**
 * Badge Component: Displays the current operational state of the CAP state machine.
 * Maps backend states (ready, fallback, etc.) to specific semantic colors.
 */
function Badge({ state }) {
  const colors = {
    ready: "#28a745",                // Green for stable/ready state
    awaiting_confirmation: "#ffb400", // Yellow for pending EA confirmation
    fallback: "#dc3545",             // Red for fallback recovery routing
    error: "#c82333",                // Dark Red for critical system failures
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
  // Local UI state for handling the current text input value
  const [input, setInput] = useState("");

  // Destructuring reactive states and actions from the custom agentic orchestration hook
  const {
    messages,         // Array containing the thread conversation history (user & assistant roles)
    send,             // Core orchestration function to dispatch user prompts to FastAPI backend
    loading,          // Boolean tracking asynchronous network request pendings
    chatState,        // Tracks current deterministic state machine architecture boundaries
    pendingActions,   // Real-time Dynamic Action Queue populated by backend intent parsing
    sessionId,        // Isolate session token ensuring contextual memory persistence
    resetSession,     // Clears session boundaries, flushing local memory stacks for fresh execution
    healthStatus,     // Monitors API reachability to track cold-starts on Render
  } = useChat();

  /**
   * Dispatches the raw text prompt to the FastAPI routing engine.
   * Prevents execution loops from empty or structural whitespaces.
   */
  const handleSend = () => {
    if (!input.trim()) return;
    send(input);
    setInput(""); // Optimistically clear input buffer for immediate typing readiness
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
        {/* =========================================================================
            HEADER SECTION: Displays branding, current system state, and session controls
            ========================================================================= */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "12px",
            flexWrap: "wrap",
          }}
        >
          <h2 style={{ margin: 0 }}>CAP Chat</h2>
          {/* Dynamic State Engine Validation badge */}
          {chatState && <Badge state={chatState} />}
          {/* Session Memory Retention status notification */}
          {sessionId && (
            <span style={{ marginLeft: "8px", fontSize: "0.85rem", opacity: 0.8 }}>
              Memory Active
            </span>
          )}
          {/* Clears architectural state mappings to start a completely pristine workflow */}
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

        {/* =========================================================================
            HEALTH STATUS BANNERS: Explicit network lifecycle indicators
            ========================================================================= */}
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

        {/* =========================================================================
            DYNAMIC ACTION QUEUE: Surfaces parallel tasks staged for executive verification
            ========================================================================= */}
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
                    {/* Maps parsed tool calling parameters (e.g., calendar_schedule, email_triage) */}
                    <div style={{ fontWeight: "600" }}>{a.action_type}</div>
                    {/* Displays descriptive payload strings derived from LLM structured boundaries */}
                    <div style={{ fontSize: "0.85rem", opacity: 0.8 }}>
                      {a.description || a.payload?.description || "(no description)"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================================
            CONVERSATIONAL MESSAGE CONTEXT LAYER: Displays multi-role dialogue threads
            ========================================================================= */}
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
                // Right align for User intent streams, left align for Assistant responses
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                marginBottom: "8px",
              }}
            >
              <div
                style={{
                  maxWidth: "80%",
                  // Dark terminal-grey block for agent, high-fidelity corporate blue for user
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

        {/* =========================================================================
            RENDER BACKEND COLD START WARNING BANNER: Product Empathy UX Transparency Layer
            ========================================================================= */}
        <div style={{
          background: 'rgba(161, 161, 170, 0.05)',
          border: '1px solid rgba(161, 161, 170, 0.15)',
          borderRadius: '6px',
          padding: '10px 14px',
          marginBottom: '16px'
        }}>
          <p style={{
            color: '#a1a1aa',
            fontSize: '13px',
            fontFamily: 'monospace',
            margin: 0,
            textAlign: 'center',
            lineHeight: '1.5'
          }}>
            <span style={{ color: '#bef264', fontWeight: 'bold' }}>⚡ SYSTEM NOTE:</span> If the first prompt takes ~45s, the cloud backend server is initiating a cold start. Subsequent interactions are ultra-fast (Groq Cloud Inference).
          </p>
        </div>

        {/* =========================================================================
            INTERACTION BASE LAYER: Input triggers and async throttle operations
            ========================================================================= */}
        <div style={{ display: "flex", alignItems: "center" }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type message..."
            disabled={loading} // Freezes input mutations during inflight asynchronous API request routing
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
            disabled={loading} // Intercepts button spamming while processing model generations
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