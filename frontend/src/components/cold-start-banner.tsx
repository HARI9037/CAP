"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

export function ColdStartBanner() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) {
    return null;
  }

  return (
    <div className="border-b border-border bg-card/60 px-4 py-3 md:px-6">
      <div className="flex items-start justify-between gap-3 rounded-md border border-border bg-background/80 px-3 py-2 text-sm text-muted-foreground shadow-sm">
        <p className="leading-6">
          <span className="font-medium text-foreground">Heads up:</span> our backend runs on a free tier and may take
          10-20 seconds to wake up if idle. If a message is slow or fails once, try again; it usually works right after.
        </p>
        <Button
          aria-label="Dismiss backend wake-up notice"
          className="h-8 w-8 shrink-0 px-0"
          onClick={() => setIsVisible(false)}
          variant="ghost"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
