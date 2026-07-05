import * as React from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
}

export function ChatInput({ value, onChange, onSubmit, loading = false }: ChatInputProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!loading) {
        onSubmit();
      }
    }
  };

  return (
    <form
      className="rounded-2xl border border-border bg-card/80 p-4 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        if (!loading) {
          onSubmit();
        }
      }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <div className="flex-1">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Message
          </label>
          <Textarea
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows={2}
            disabled={loading}
            className="min-h-20 resize-none border-border bg-background text-foreground placeholder:text-muted-foreground"
          />
        </div>
        <Button type="submit" disabled={loading} className="md:min-w-28">
          {loading ? "Sending..." : "Send"}
        </Button>
      </div>
    </form>
  );
}
