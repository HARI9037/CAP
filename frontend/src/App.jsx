import { useState, useEffect, useRef } from "react";
import { useChat } from "./useChat";
import MessageContent from "./MessageContent";
import SessionInsightPanel from "./SessionInsightPanel";

export default function App() {
  const [input, setInput] = useState("");
  const [sessionPanelOpen, setSessionPanelOpen] = useState(false);
  const [coldStartNoticeOpen, setColdStartNoticeOpen] = useState(() => {
    return localStorage.getItem("cap_cold_start_notice_seen") !== "true";
  });
  const {
    messages,
    send,
    loading,
    chatState,
    sessionPhase,
    pendingActions,
    memorySummary,
    lastError,
    lastApiResult,
    lastReply,
    sessionId,
    resetSession,
    healthStatus,
    sessions,
    loadSession,
    performDeleteSession,
  } = useChat();

  const messagesEndRef = useRef(null);

  // Automatically scroll to the bottom of the chat on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    send(input.trim());
    setInput("");
  };

  const dismissColdStartNotice = () => {
    localStorage.setItem("cap_cold_start_notice_seen", "true");
    setColdStartNoticeOpen(false);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0A0F1E]">

      {/* LEFT SIDEBAR: SESSION MANAGER */}
      <div className="w-[260px] flex-shrink-0 bg-[#0D1424] border-r border-[#1E293B] flex flex-col h-full justify-between select-none">
        <div className="flex flex-col flex-1 overflow-hidden">

          {/* Logo Heading */}
          <div className="h-[56px] flex items-center px-4 border-b border-[#1E293B] flex-shrink-0">
            <span className="text-[18px] font-bold text-white">CAP</span>
            <span className="text-[18px] font-bold text-[#06B6D4] ml-1">// OS</span>
          </div>

          {/* Session History Feed */}
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
                    className={`group min-h-[44px] px-4 py-2 flex items-center justify-between cursor-pointer transition-colors duration-150 ${isActive
                        ? "bg-[#1E293B] border-l-2 border-[#06B6D4]"
                        : "border-l-2 border-transparent hover:bg-[#151f33]"
                      }`}
                  >
                    <div className="flex flex-col justify-center min-w-0 flex-1">
                      <div className="text-[13px] text-white truncate font-normal leading-tight">
                        {session.title}
                      </div>
                      <div className="text-[11px] text-[#64748B] mt-0.5 leading-none">
                        {session.time}
                      </div>
                    </div>

                    {/* Inline Hover Delete Trigger Button */}
                    <button
                      onClick={(e) => performDeleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-[#64748B] hover:text-red-400 text-[12px] pl-2 transition-all font-bold"
                      title="Delete Session"
                    >
                      ✕
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: MAIN WORKSPACE */}
      <div className="flex flex-1 flex-col min-w-0">

        {/* TOP STATUS CONTROL BAR */}
        <div className="h-[56px] flex-shrink-0 bg-[#0D1424] border-b border-[#1E293B] flex items-center justify-between px-6 select-none">
          <div className="text-[15px] font-medium text-white truncate max-w-[400px]">
            {sessions.find((s) => s.id === sessionId)?.title || "New Chat Session"}
          </div>

          <div className="flex items-center gap-3">
            {/* Live Polling Engine Badge Status Indicator */}
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
              onClick={() => setSessionPanelOpen(true)}
              className="xl:hidden border border-[#1E293B] text-slate-300 text-[13px] bg-[#111827] rounded-md px-3 py-1.5 hover:border-[#06B6D4] hover:text-[#06B6D4] transition-colors duration-150 font-medium"
            >
              Session
            </button>

            <div className="hidden xl:block w-px h-5 bg-[#1E293B]" />

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

        {/* MIDDLE LOG VIEWPORT AREA */}
        <div className="flex-1 overflow-y-auto flex flex-col bg-[#0A0F1E]">

          {/* PENDING ACTIONS SUBPANEL */}
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

          {/* MESSAGES LAYER OR DEFAULT WELCOME LANDING STATE */}
          {messages.length === 0 && !loading ? (
            <div className="flex flex-col items-center justify-center flex-1 p-6 text-center select-none">
              <div className="text-[#06B6D4] text-[32px] font-bold tracking-tight">CAP</div>
              <div className="text-[#64748B] text-[14px] mt-1 font-medium">Context-Aware Partner</div>
              <div className="text-[#64748B] text-[13px] mt-4">Start a conversation to begin.</div>
            </div>
          ) : (
            <div className="px-6 py-4 flex flex-col gap-6 flex-1">
              {messages.map((msg, index) => {
                const isUser = msg.role === "user" || msg.sender === "user";
                const content = msg.content || msg.text || msg.message || "";

                if (!content) return null;

                if (isUser) {
                  return (
                    <div key={index} className="flex justify-end w-full">
                      <div className="bg-[#06B6D4] text-white text-[14px] rounded-xl rounded-tr-sm px-5 py-4 max-w-[60%] leading-relaxed break-words shadow-sm font-normal whitespace-pre-wrap">
                        {content}
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
                      <div className="bg-[#111827] border border-[#1E293B] border-l-2 border-l-[#06B6D4] text-slate-100 text-[14px] rounded-xl rounded-tl-sm px-5 py-4 max-w-[72%] leading-7 break-words shadow-sm font-normal">
                        <MessageContent content={content} />
                      </div>
                    </div>
                  );
                }
              })}

              {/* ACTIVE STREAM PROCESSING LOADER */}
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

        {/* BOTTOM USER DISPATCH INTERACTION BAR */}
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

        {/* SYSTEM STATUS FOOTNOTE */}
        <div className="py-2 text-center bg-[#0A0F1E] flex-shrink-0 select-none border-t border-[#1E293B]/20">
          <p className="text-[#64748B] text-[11px] italic">
            CAP is in restricted mode. Actions require manual approval.
          </p>
        </div>
      </div>

      <SessionInsightPanel
        chatState={chatState}
        healthStatus={healthStatus}
        lastApiResult={lastApiResult}
        lastError={lastError}
        lastReply={lastReply}
        loading={loading}
        memorySummary={memorySummary}
        messages={messages}
        pendingActions={pendingActions}
        sessionPhase={sessionPhase}
        sessionId={sessionId}
      />

      {sessionPanelOpen && (
        <div className="fixed inset-0 z-50 flex items-end bg-black/50 xl:hidden">
          <button
            className="absolute inset-0 cursor-default"
            aria-label="Close session panel"
            onClick={() => setSessionPanelOpen(false)}
          />
          <div className="relative w-full px-3 pb-3">
            <div className="mb-2 flex justify-end">
              <button
                onClick={() => setSessionPanelOpen(false)}
                className="rounded-full border border-[#1E293B] bg-[#0D1424] px-3 py-1.5 text-[12px] font-semibold uppercase tracking-wider text-slate-300"
              >
                Close
              </button>
            </div>
            <SessionInsightPanel
              chatState={chatState}
              healthStatus={healthStatus}
              lastApiResult={lastApiResult}
              lastError={lastError}
              lastReply={lastReply}
              loading={loading}
              memorySummary={memorySummary}
              messages={messages}
              pendingActions={pendingActions}
              sessionPhase={sessionPhase}
              sessionId={sessionId}
              variant="drawer"
            />
          </div>
        </div>
      )}

      {coldStartNoticeOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-[420px] rounded-lg border border-[#1E293B] bg-[#0D1424] p-5 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full bg-[#F59E0B] shadow-[0_0_18px_rgba(245,158,11,0.65)]" />
              <div className="min-w-0">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#F59E0B]">
                  Backend Wake-Up Notice
                </div>
                <h2 className="mt-2 text-[18px] font-semibold text-white">
                  CAP may take a moment to connect
                </h2>
                <p className="mt-3 text-[13px] leading-6 text-slate-300">
                  This demo uses Render for the backend. If the service has been idle, the first message may need about 45-60 seconds while the API wakes up.
                </p>
                <div className="mt-4 rounded-md border border-[#1E293B] bg-[#0A0F1E]/70 px-3 py-2 text-[12px] leading-5 text-slate-400">
                  After the first response, follow-up messages should feel much faster.
                </div>
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={dismissColdStartNotice}
                className="rounded-md bg-[#06B6D4] px-4 py-2 text-[12px] font-semibold uppercase tracking-wider text-white transition-opacity duration-150 hover:opacity-90"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
