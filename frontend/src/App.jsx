import { useState, useEffect, useRef } from "react";
import { useChat } from "./useChat";

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
    sessions,
    loadSession,
  } = useChat();

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    send(input.trim());
    setInput("");
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0A0F1E]">
      {/* LEFT SIDEBAR */}
      <div className="w-[260px] flex-shrink-0 bg-[#0D1424] border-r border-[#1E293B] flex flex-col h-full justify-between select-none">
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* TOP SECTION: Logo Area */}
          <div className="h-[56px] flex items-center px-4 border-b border-[#1E293B] flex-shrink-0">
            <span className="text-[18px] font-bold text-white">CAP</span>
            <span className="text-[18px] font-bold text-[#06B6D4] ml-1">// OS</span>
          </div>

          {/* PAST SESSIONS SECTION (PRIORITY 1 FIX: Connected to dynamic localStorage) */}
          <div className="flex-1 overflow-y-auto pt-4 pb-2">
            <div className="text-[10px] uppercase text-[#64748B] tracking-wider pl-4 mb-2 font-semibold">
              PAST SESSIONS
            </div>
            <div className="flex flex-col">
              {sessions.map((session) => {
                const isActive = sessionId === session.id;
                return (
                  <div
                    key={session.id}
                    onClick={() => loadSession(session.id)}
                    className={`min-h-[40px] px-4 py-2 flex flex-col justify-center cursor-pointer transition-colors duration-150 ${isActive
                      ? "bg-[#1E293B] border-l-2 border-[#06B6D4]"
                      : "border-l-2 border-transparent hover:bg-[#151f33]"
                      }`}
                  >
                    <div className="text-[13px] text-white truncate font-normal leading-tight">
                      {session.title}
                    </div>
                    <div className="text-[11px] text-[#64748B] mt-0.5 leading-none">
                      {session.time}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* PRIORITY 3 FIX: Bottom Profile section block completely removed from here */}
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex flex-1 flex-col min-w-0">

        {/* TOP HEADER BAR */}
        <div className="h-[56px] flex-shrink-0 bg-[#0D1424] border-b border-[#1E293B] flex items-center justify-between px-6 select-none">
          {/* LEFT SIDE: Dynamic Session Title Display */}
          <div className="text-[15px] font-medium text-white">
            {sessions.find((s) => s.id === sessionId)?.title || "New Chat Session"}
          </div>

          {/* RIGHT SIDE: System Controls & Indicators */}
          <div className="flex items-center gap-3">
            {/* Backend status pill (PRIORITY 2 FIX: True state reactive verification toggling) */}
            <div className="bg-[#111827] border border-[#1E293B] rounded-full px-3 py-1 flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${healthStatus === "ready" ? "bg-[#10B981]" : "bg-[#EF4444]"
                  }`}
              />
              <span
                className={`text-[11px] uppercase tracking-wider font-semibold ${healthStatus === "ready" ? "text-[#10B981]" : "text-[#EF4444]"
                  }`}
              >
                {healthStatus === "ready" ? "BACKEND READY" : "BACKEND UNAVAILABLE"}
              </span>
            </div>

            <div className="w-px h-5 bg-[#1E293B]" />

            <button
              onClick={resetSession}
              className="border border-[#06B6D4] text-[#06B6D4] text-[13px] bg-transparent rounded-md px-3 py-1.5 hover:bg-[#06b6d4]/10 transition-colors duration-150 font-medium"
            >
              New Session
            </button>

            <div className="w-px h-5 bg-[#1E293B]" />

            <div className="w-[34px] h-[34px] rounded-full bg-[#06B6D4] flex items-center justify-center text-white text-[12px] font-bold cursor-pointer hover:opacity-90 transition-opacity">
              ST
            </div>
          </div>
        </div>

        {/* MIDDLE CHAT FEED AREA */}
        <div className="flex-1 overflow-y-auto flex flex-col bg-[#0A0F1E]">
          {/* PENDING ACTIONS PANEL */}
          {pendingActions && pendingActions.length > 0 && (
            <div className="mx-6 mt-6 mb-4 bg-[#111827] border border-[#1E293B] border-l-4 border-l-[#06B6D4] rounded-lg p-4 flex-shrink-0">
              <div className="flex items-center gap-2 select-none">
                <span className="text-[#06B6D4] text-[14px] font-bold">✓</span>
                <span className="text-white text-[13px] font-semibold">Pending Actions</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3">
                {pendingActions.map((action, idx) => (
                  <div
                    key={action.action_id || idx}
                    className="bg-[#0D1424] border border-[#1E293B] border-l-2 border-l-[#06B6D4] rounded-md p-3 relative flex flex-col justify-between"
                  >
                    <div className="flex justify-between items-center select-none">
                      <span className="text-[10px] uppercase tracking-wider text-[#06B6D4] border border-[#06B6D4] rounded px-2 py-0.5 font-semibold">
                        {action.action_type}
                      </span>
                      <span className="text-[#64748B] text-[14px]">→</span>
                    </div>
                    <div className="text-white text-[13px] font-semibold mt-2 break-words">
                      {action.description}
                    </div>
                    <div className="text-[#64748B] text-[11px] mt-1 uppercase tracking-tight font-medium">
                      {action.action_type}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CHAT MESSAGES STREAM OR EMPTY VIEW STATE */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center flex-1 p-6 text-center select-none">
              <div className="text-[#06B6D4] text-[32px] font-bold tracking-tight">CAP</div>
              <div className="text-[#64748B] text-[14px] mt-1 font-medium">Context-Aware Partner</div>
              <div className="text-[#64748B] text-[13px] mt-4">Start a conversation to begin.</div>
            </div>
          ) : (
            <div className="px-6 py-4 flex flex-col gap-6 flex-1">
              {messages.map((msg, index) => {
                if (msg.role === "user") {
                  return (
                    <div key={index} className="flex justify-end w-full">
                      <div className="bg-[#06B6D4] text-white text-[14px] rounded-xl rounded-tr-sm px-4 py-3 max-w-[60%] leading-relaxed break-words shadow-sm font-normal">
                        {msg.content}
                      </div>
                    </div>
                  );
                } else {
                  return (
                    <div key={index} className="flex flex-col items-start w-full">
                      <div className="flex items-center gap-1.5 mb-1 select-none">
                        <span className="text-[#06B6D4] text-[12px]">◈</span>
                        <span className="text-[#06B6D4] text-[11px] uppercase tracking-wider font-semibold">
                          CAP
                        </span>
                      </div>
                      <div className="bg-[#111827] border border-[#1E293B] border-l-2 border-l-[#06B6D4] text-white text-[14px] rounded-xl rounded-tl-sm px-4 py-3 max-w-[70%] leading-relaxed break-words shadow-sm font-normal">
                        {msg.content}
                      </div>
                    </div>
                  );
                }
              })}

              {/* TYPING LOADER */}
              {loading && (
                <div className="flex flex-col items-start w-full">
                  <div className="flex items-center gap-1.5 mb-1 select-none">
                    <span className="text-[#06B6D4] text-[12px]">◈</span>
                    <span className="text-[#06B6D4] text-[11px] uppercase tracking-wider font-semibold">
                      CAP
                    </span>
                  </div>
                  <div className="bg-[#111827] border border-[#1E293B] rounded-xl px-4 py-3 shadow-sm select-none">
                    <span className="text-[#64748B] text-[18px] tracking-widest font-bold block leading-none pb-1 animate-pulse">
                      • • •
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* BOTTOM INPUT BAR */}
        <div className="min-h-[80px] flex-shrink-0 bg-[#0D1424] border-t border-[#1E293B] flex items-center px-6 gap-3">
          <span className="text-[#64748B] text-[18px] cursor-pointer select-none hover:text-white transition-colors">
            📎
          </span>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type a message..."
            className="flex-1 bg-transparent border-none outline-none text-white text-[14px] placeholder-[#64748B]"
          />

          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-[#06B6D4] text-white rounded-lg px-4 py-2 flex items-center gap-2 text-[12px] uppercase tracking-wider font-semibold transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 flex-shrink-0"
          >
            SEND <span>→</span>
          </button>
        </div>

        {/* FOOTNOTE */}
        <div className="py-2 text-center bg-[#0A0F1E] flex-shrink-0 select-none border-t border-[#1E293B]/20">
          <p className="text-[#64748B] text-[11px] italic">
            CAP is in restricted mode. Actions require manual approval.
          </p>
        </div>
      </div>
    </div>
  );
}