function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

function StatusPill({ tone = "slate", children }) {
  const tones = {
    green: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    cyan: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    red: "border-red-500/30 bg-red-500/10 text-red-300",
    slate: "border-slate-600/60 bg-slate-800/40 text-slate-300",
  };

  return (
    <span className={cx("rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider", tones[tone])}>
      {children}
    </span>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-md border border-[#1E293B] bg-[#0A0F1E]/60 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">{label}</div>
      <div className="mt-1 truncate text-[13px] font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function displayState(chatState, loading, healthStatus, lastError) {
  if (healthStatus !== "ready") return { label: "Offline", tone: "red" };
  if (chatState === "offline" || lastError === "network_error") return { label: "Offline", tone: "red" };
  if (loading) return { label: "Thinking", tone: "cyan" };
  if (lastError || chatState === "fallback") return { label: "Fallback", tone: "amber" };
  return { label: "Ready", tone: "green" };
}

function phaseLabel(sessionPhase, chatState, sessionId) {
  if (!sessionId) return "no_session";
  return sessionPhase || chatState || "general_chat";
}

function lastActivity({ loading, lastError, lastReply, pendingActions }) {
  if (loading) return "CAP is processing the latest message.";
  if (lastError) return "CAP used a safe fallback for the last turn.";
  if (pendingActions.length > 0) return "CAP proposed actions and is waiting for approval.";
  if (lastReply) return "CAP answered and saved the turn to session memory.";
  return "No active session yet.";
}

function resultLabel(result, sessionId) {
  if (!result) return sessionId ? "No Result" : "Idle";

  const labels = {
    groq_api_failure: "API Error",
    groq_configuration_missing: "Config Missing",
    groq_timeout: "Timeout",
    llm_parse_failure: "Parse Fallback",
    memory_load_failed: "Memory Error",
    network_error: "Network Error",
  };

  return labels[result.label] || result.label;
}

export default function SessionInsightPanel({
  chatState,
  healthStatus,
  lastApiResult,
  lastError,
  lastReply,
  loading,
  memorySummary,
  messages,
  pendingActions,
  sessionPhase,
  sessionId,
  variant = "rail",
}) {
  const actions = Array.isArray(pendingActions) ? pendingActions : [];
  const status = displayState(chatState, loading, healthStatus, lastError);
  const summary = memorySummary?.summary || "Session memory will appear after CAP responds.";
  const messageCount = memorySummary?.message_count ?? messages.length;
  const sessionShort = sessionId ? `${sessionId.slice(0, 8)}...` : "none";
  const apiResultLabel = resultLabel(lastApiResult, sessionId);
  const apiResultTone = lastApiResult ? (lastApiResult.ok === false ? "amber" : "green") : "slate";
  const hasMemory = Boolean(memorySummary?.summary || memorySummary?.session_id || sessionId);

  return (
    <aside
      className={cx(
        "bg-[#0D1424] text-slate-100",
        variant === "rail"
          ? "hidden w-[300px] flex-shrink-0 border-l border-[#1E293B] xl:flex xl:flex-col"
          : "flex max-h-[70vh] flex-col rounded-t-2xl border border-[#1E293B] shadow-2xl"
      )}
    >
      <div className="border-b border-[#1E293B] px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#64748B]">
              Live Session
            </div>
            <div className="mt-1 text-[15px] font-semibold text-white">CAP Runtime</div>
          </div>
          <StatusPill tone={status.tone}>{status.label}</StatusPill>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <StatusPill tone={healthStatus === "ready" ? "green" : "red"}>
            {healthStatus === "ready" ? "API Ready" : "API Offline"}
          </StatusPill>
          <StatusPill tone={hasMemory ? "cyan" : "slate"}>
            {hasMemory ? "Memory Active" : "Memory Idle"}
          </StatusPill>
          <StatusPill tone={actions.length ? "amber" : "green"}>
            {actions.length ? `${actions.length} Pending` : "No Pending Actions"}
          </StatusPill>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        <div className="grid grid-cols-2 gap-2">
          <Metric label="Session" value={sessionShort} />
          <Metric label="Messages" value={messageCount} />
          <Metric label="Phase" value={phaseLabel(sessionPhase, chatState, sessionId)} />
          <Metric label="Actions" value={actions.length} />
        </div>

        <section className="rounded-md border border-[#1E293B] bg-[#0A0F1E]/60 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
              Last Backend Result
            </span>
            <StatusPill tone={apiResultTone}>{apiResultLabel}</StatusPill>
          </div>
          <p className="text-[12px] leading-5 text-slate-300">
            {sessionId ? "Latest API response has been folded into the session view." : "No active session yet."}
          </p>
        </section>

        <section className="rounded-md border border-[#1E293B] bg-[#0A0F1E]/60 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
              What CAP just did
            </span>
            <StatusPill tone={lastError ? "amber" : "slate"}>
              {lastError ? "Fallback Used" : "Synced"}
            </StatusPill>
          </div>
          <p className="text-[12px] leading-5 text-slate-300">
            {lastActivity({ loading, lastError, lastReply, pendingActions: actions })}
          </p>
        </section>

        <section className="rounded-md border border-[#1E293B] bg-[#0A0F1E]/60 p-3">
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
            Memory Summary
          </div>
          <p className="line-clamp-5 text-[12px] leading-5 text-slate-300">{summary}</p>
        </section>

        <section className="rounded-md border border-[#1E293B] bg-[#0A0F1E]/60 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
              Pending Actions
            </span>
            <StatusPill tone={actions.length ? "amber" : "green"}>
              {actions.length ? `${actions.length} Pending` : "None"}
            </StatusPill>
          </div>

          {actions.length > 0 ? (
            <div className="space-y-2">
              {actions.slice(0, 3).map((action, index) => (
                <div key={action.action_id || index} className="border-l border-cyan-400/70 pl-2">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300">
                    {action.action_type || "action"}
                  </div>
                  <div className="mt-1 line-clamp-2 text-[12px] leading-5 text-slate-300">
                    {action.description || "Awaiting approval."}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[12px] leading-5 text-slate-400">No approval requests are waiting.</p>
          )}
        </section>
      </div>
    </aside>
  );
}
