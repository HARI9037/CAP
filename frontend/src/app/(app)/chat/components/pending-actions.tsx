import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { PendingAction } from "./types";

interface PendingActionsProps {
  actions: PendingAction[];
  onApprove: (action: PendingAction) => void;
  onReject: (action: PendingAction) => void;
  disabled?: boolean;
}

export function PendingActions({ actions, onApprove, onReject, disabled = false }: PendingActionsProps) {
  if (actions.length === 0) return null;

  return (
    <div className="mt-4 grid gap-3 md:grid-cols-2">
      {actions.map((action) => (
        <Card key={action.action_id} className="border-cyan-500/20 bg-[#0A0F1E]/60">
          <CardHeader className="space-y-2 pb-3">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-sm font-semibold text-slate-100">
                {action.action_type || "Action"}
              </CardTitle>
              <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-300">
                Pending
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-6 text-slate-300">
              {action.description || "Awaiting approval."}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => onApprove(action)} disabled={disabled}>
                Approve
              </Button>
              <Button size="sm" variant="outline" onClick={() => onReject(action)} disabled={disabled}>
                Reject
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
