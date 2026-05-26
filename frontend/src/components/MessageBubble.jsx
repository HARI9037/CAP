import { formatTimestamp } from "../utils/formatters";

function MessageBubble({ role, content, timestamp }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-md px-4 py-3 text-sm leading-relaxed ${
          isUser ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-100"
        }`}
      >
        <p className="m-0 whitespace-pre-wrap">{content}</p>
        <p className="mt-2 text-right text-xs text-slate-300">{formatTimestamp(timestamp)}</p>
      </div>
    </div>
  );
}

export default MessageBubble;
