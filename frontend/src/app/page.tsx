import Link from "next/link";
import { ArrowRight, CheckCircle2, History, Lock, MessageSquare, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";

const features = [
  "Persistent Memory",
  "Context Awareness",
  "Confirmation-Gated Actions",
  "Decision Support",
  "Conversation History"
];

const steps = ["Talk naturally", "CAP learns relevant context", "CAP helps you think through decisions", "You stay in control"];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="relative overflow-hidden border-b">
        <div className="mx-auto grid min-h-[82vh] max-w-7xl content-center gap-10 px-6 py-20 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="max-w-3xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-md border px-3 py-1 text-sm text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Human-in-the-loop AI partner
            </div>
            <h1 className="max-w-4xl text-5xl font-semibold tracking-normal md:text-7xl">Think Better Before You Act</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
              CAP is a context-aware AI partner that remembers what matters and helps you make decisions with confidence.
            </p>
            <Button asChild className="mt-8">
              <Link href="/dashboard">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="rounded-lg border bg-card p-4 shadow-2xl">
            <div className="mb-4 flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2 font-medium">
                <MessageSquare className="h-4 w-4 text-primary" />
                Decision workspace
              </div>
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="space-y-3 text-sm">
              <div className="rounded-md bg-muted p-3">I’m considering changing the roadmap. What should I weigh first?</div>
              <div className="rounded-md border p-3 text-muted-foreground">
                I’ll compare this against your stored goals, project context, and prior tradeoffs before recommending next steps.
              </div>
              <div className="rounded-md border border-primary/40 bg-primary/10 p-3">
                Confirmation required before saving the new roadmap memory.
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-4 md:grid-cols-5">
          {features.map((feature) => (
            <div key={feature} className="rounded-lg border bg-card p-4 text-sm font-medium">
              <CheckCircle2 className="mb-3 h-5 w-5 text-primary" />
              {feature}
            </div>
          ))}
        </div>
      </section>
      <section className="border-y bg-card/40">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <h2 className="text-2xl font-semibold">How It Works</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {steps.map((step, index) => (
              <div key={step} className="rounded-lg border bg-background p-5">
                <div className="mb-5 flex h-8 w-8 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground">
                  {index + 1}
                </div>
                <p className="font-medium">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-lg border bg-card p-6 text-muted-foreground">
          “CAP feels like a thinking partner that asks before it changes anything.” Testimonials placeholder.
        </div>
      </section>
      <footer className="border-t px-6 py-8 text-center text-sm text-muted-foreground">
        <History className="mx-auto mb-2 h-4 w-4" />
        CAP remembers context so you can make better calls.
      </footer>
    </main>
  );
}
