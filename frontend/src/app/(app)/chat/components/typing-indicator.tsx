export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[min(42rem,92%)] rounded-2xl border border-border bg-card px-4 py-3 text-card-foreground shadow-sm">
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          CAP
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.2s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.1s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
          <span className="ml-2 text-sm text-muted-foreground">Thinking...</span>
        </div>
      </div>
    </div>
  );
}
