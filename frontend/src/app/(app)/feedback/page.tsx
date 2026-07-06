"use client";

import { FormEvent, useState } from "react";
import { MessageSquare, Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useClerkApiRequest } from "@/lib/api";
import { cn } from "@/lib/utils";

type FeedbackResponse = {
  ok: boolean;
  feedback: {
    feedback_id: string;
    rating: number;
    comment: string;
    created_at: string;
  };
};

const ratings = [1, 2, 3, 4, 5];

export default function FeedbackPage() {
  const apiRequest = useClerkApiRequest();
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await apiRequest<FeedbackResponse>("/feedback", {
        method: "POST",
        body: JSON.stringify({ rating, comment }),
      });
      setSuccess(`Feedback saved. Reference ${result.feedback.feedback_id.slice(0, 8)}...`);
      setComment("");
      setRating(5);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit feedback");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex-1 p-6">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        <div className="border-b border-border pb-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Product signal
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">Feedback</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Share what is working, what is confusing, or what should change next.
          </p>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        ) : null}

        {success ? (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-200">
            {success}
          </div>
        ) : null}

        <Card className="border-border bg-card/80 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              Send feedback
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={submitFeedback}>
              <div>
                <div className="mb-2 text-sm font-medium">Rating</div>
                <div className="grid grid-cols-5 gap-2">
                  {ratings.map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setRating(value)}
                      className={cn(
                        "flex h-12 items-center justify-center gap-1 rounded-md border border-border bg-background text-sm font-medium transition-colors hover:bg-muted",
                        rating === value && "border-primary bg-primary/10 text-primary"
                      )}
                      aria-pressed={rating === value}
                    >
                      <Star className="h-4 w-4" />
                      {value}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="feedback-comment" className="mb-2 block text-sm font-medium">
                  Comment
                </label>
                <Textarea
                  id="feedback-comment"
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  maxLength={4000}
                  placeholder="Tell us what happened or what would make CAP better."
                  className="min-h-36"
                />
                <div className="mt-2 text-xs text-muted-foreground">{comment.length}/4000</div>
              </div>

              <Button type="submit" disabled={submitting}>
                {submitting ? "Submitting..." : "Submit feedback"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
