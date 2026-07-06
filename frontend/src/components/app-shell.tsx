"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, History, MessageSquarePlus, Settings, Star, Database } from "lucide-react";

import { AuthControls } from "@/components/auth-controls";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const nav = [
  { href: "/chat", label: "New Chat", icon: MessageSquarePlus },
  { href: "/history", label: "History", icon: History },
  { href: "/memory", label: "Memory", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/feedback", label: "Feedback", icon: Star }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 border-r bg-card/60 p-4 md:block">
        <Link href="/" className="mb-8 flex items-center gap-2 text-lg font-semibold">
          <Brain className="h-5 w-5 text-primary" />
          CAP
        </Link>
        <nav className="space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.href}
                asChild
                variant="ghost"
                className={cn("w-full justify-start", pathname === item.href && "bg-muted")}
              >
                <Link href={item.href}>
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              </Button>
            );
          })}
        </nav>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b px-4 md:px-6">
          <Link href="/chat" className="flex items-center gap-2 font-semibold md:hidden">
            <Brain className="h-5 w-5 text-primary" />
            CAP
          </Link>
          <div className="hidden text-sm text-muted-foreground md:block">Context-aware decisions, confirmation first.</div>
          <div className="flex items-center gap-2">
            <AuthControls />
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
