import Link from "next/link";
import { ArrowRight, Database, History, MessageSquarePlus, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const statusItems = [
  { label: "Auth", value: "Clerk connected", detail: "Bearer tokens are sent with protected requests." },
  { label: "Backend", value: "Render ready", detail: "Health checks stay public while user data stays protected." },
  { label: "Memory", value: "User scoped", detail: "Sessions are isolated by authenticated Clerk user ID." }
];

const nextActions = [
  { href: "/chat", label: "Start a chat", icon: MessageSquarePlus },
  { href: "/history", label: "Review history", icon: History },
  { href: "/memory", label: "Inspect memory", icon: Database }
];

export default function DashboardPage() {
  return (
    <section className="flex-1 p-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-4 border-b pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Monitor CAP readiness, continue active work, and move into the authenticated tools that are ready for the demo.
            </p>
          </div>
          <Button asChild>
            <Link href="/chat">
              <MessageSquarePlus className="h-4 w-4" />
              New chat
            </Link>
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {statusItems.map((item) => (
            <Card key={item.label}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-sm">
                  {item.label}
                  <ShieldCheck className="h-4 w-4 text-primary" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-semibold">{item.value}</div>
                <p className="mt-2 text-sm text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Deployment Readiness</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md border p-4">
                <div className="text-sm font-medium">Protected workflow available</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  The dashboard now gives signed-in users a real starting point instead of a placeholder screen.
                </p>
              </div>
              <div className="rounded-md border p-4">
                <div className="text-sm font-medium">Confirmation-first posture</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  CAP can propose actions while keeping approval and memory review visible from the main workspace.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Continue</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {nextActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Button key={action.href} asChild variant="outline" className="w-full justify-between">
                    <Link href={action.href}>
                      <span className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        {action.label}
                      </span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
