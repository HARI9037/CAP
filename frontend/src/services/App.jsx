import { useState } from "react";
import { useChat } from "./hooks/useChat";

function App() {
    const [input, setInput] = useState("");
    const { messages, send, loading } = useChat();

    return (
        <div style={{ padding: 20 }}>
            <h2>CAP Chat</h2>

            <div>
                {messages.map((m, i) => (
                    <div key={i}>
                        <b>{m.role}:</b> {m.content}
                    </div>
                ))}
            </div>

            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type message..."
            />

            <button
                onClick={() => {
                    send(input);
                    setInput("");
                }}
            >
                {loading ? "..." : "Send"}
            </button>
        </div>
    );
}

export default App;