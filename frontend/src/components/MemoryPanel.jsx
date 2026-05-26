import { formatTimestamp, truncateText } from "../utils/formatters";

function MemoryPanel({ summary, isLoading }) {
  return (
    <aside className="rounded-md border border-slate-800 bg-slate-900 p-4">
      <h2 className="m-0 text-sm font-semibold text-slate-100">Memory Summary</h2>
      {isLoading ? (
        <p className="mt-3 text-sm text-slate-300">Refreshing memory...</p>
      ) : (
        <div className="mt-3 space-y-2 text-sm text-slate-300">
          <p className="m-0">
            Session: <span className="text-slate-100">{summary.session_id ?? "none"}</span>
          </p>
          <p className="m-0">
            Messages: <span className="text-slate-100">{summary.message_count ?? 0}</span>
          </p>
          <p className="m-0">
            Updated: <span className="text-slate-100">{formatTimestamp(summary.updated_at)}</span>
          </p>
          <p className="m-0 text-xs text-slate-400">{truncateText(summary.summary || "No summary yet.", 140)}</p>
        </div>
      )}
    </aside>
  );
}

export default MemoryPanel;
