import { useState } from "react";

import ChatWindow from "../components/ChatWindow";
import ConfirmationCard from "../components/ConfirmationCard";
import MemoryPanel from "../components/MemoryPanel";
import WarmupScreen from "../components/WarmupScreen";
import useChat from "../hooks/useChat";
import useConfirmation from "../hooks/useConfirmation";
import useHealthCheck from "../hooks/useHealthCheck";
import useMemory from "../hooks/useMemory";

function HomePage() {
  const { isReady, errorMessage } = useHealthCheck();
  const { messages, pendingActions, isSending, sendPrompt, sessionId } = useChat();
  const { summary, isLoading: isMemoryLoading, refresh } = useMemory(sessionId, isReady);
  const { isSubmitting, submitConfirmation } = useConfirmation();
  const [prompt, setPrompt] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) {
      return;
    }
    setPrompt("");
    const response = await sendPrompt(trimmed);
    if (response.ok) {
      refresh();
    }
  };

  const handleResolveAction = async (actionId, actionType, approved) => {
    await submitConfirmation(actionId, actionType, approved);
  };

  if (!isReady) {
    return <WarmupScreen errorMessage={errorMessage} />;
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
      <section className="mx-auto grid w-full max-w-6xl gap-4 md:grid-cols-[2fr_1fr]">
        <div className="space-y-4">
          <header>
            <h1 className="m-0 text-2xl font-semibold">CAP</h1>
            <p className="mt-1 text-sm text-slate-400">Context-Aware Partner</p>
          </header>
          <ChatWindow messages={messages} />
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask CAP to continue your workflow..."
              className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none ring-sky-500 focus:ring"
            />
            <button
              type="submit"
              disabled={isSending}
              className="rounded-md bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-slate-700"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </form>
          <ConfirmationCard
            actions={pendingActions}
            onResolve={handleResolveAction}
            isSubmitting={isSubmitting}
          />
        </div>
        <MemoryPanel summary={summary} isLoading={isMemoryLoading} />
      </section>
    </main>
  );
}

export default HomePage;
