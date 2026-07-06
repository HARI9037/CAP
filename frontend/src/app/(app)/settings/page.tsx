"use client";

import { useEffect, useState } from "react";
import { Mail, SlidersHorizontal, User } from "lucide-react";
import { useUser } from "@clerk/nextjs";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useClerkApiRequest } from "@/lib/api";

type SettingsResponse = {
  ok: boolean;
  settings: {
    theme: string;
    model: string;
    memory_enabled: boolean;
    confirmation_required: boolean;
    verbose_replies: boolean;
    updated_at: string;
  };
};

type ToggleKey = "confirmation_required" | "verbose_replies";

export default function SettingsPage() {
  const { user, isLoaded } = useUser();
  const apiRequest = useClerkApiRequest();
  const [settings, setSettings] = useState<SettingsResponse["settings"] | null>(null);
  const [savingKey, setSavingKey] = useState<ToggleKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      setLoading(true);
      setError(null);

      try {
        const result = await apiRequest<SettingsResponse>("/settings");
        if (!active) return;
        setSettings(result.settings);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSettings();

    return () => {
      active = false;
    };
  }, []);

  async function updateToggle(key: ToggleKey, value: boolean) {
    if (!settings) return;

    const previous = settings;
    setSavingKey(key);
    setError(null);
    setSettings({ ...settings, [key]: value });

    try {
      const result = await apiRequest<SettingsResponse>("/settings", {
        method: "PUT",
        body: JSON.stringify({ [key]: value }),
      });
      setSettings(result.settings);
    } catch (err) {
      setSettings(previous);
      setError(err instanceof Error ? err.message : "Could not update settings");
    } finally {
      setSavingKey(null);
    }
  }

  const email = user?.primaryEmailAddress?.emailAddress ?? "No email available";
  const name = user?.fullName || user?.username || "Signed-in user";

  return (
    <section className="flex-1 p-6">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <div className="border-b border-border pb-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Account controls
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Review your account and choose how CAP behaves during conversations.
          </p>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
            <strong className="font-semibold">Error:</strong> {error}
          </div>
        ) : null}

        <Card className="border-border bg-card/80 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              Account
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-md border border-border bg-background p-4">
              <div className="text-sm font-medium">{isLoaded ? name : "Loading account..."}</div>
              <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="h-4 w-4" />
                {isLoaded ? email : "Loading email..."}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card/80 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
              CAP Behavior
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading || !settings ? (
              <div className="rounded-md border border-dashed border-border bg-background/60 px-4 py-10 text-center text-sm text-muted-foreground">
                Loading settings...
              </div>
            ) : (
              <>
                <label className="flex cursor-pointer items-center justify-between gap-4 rounded-md border border-border bg-background p-4">
                  <span>
                    <span className="block text-sm font-medium">Require confirmation for all actions</span>
                    <span className="mt-1 block text-sm text-muted-foreground">
                      CAP asks before taking action, even for low-risk requests.
                    </span>
                  </span>
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-primary"
                    checked={settings.confirmation_required}
                    disabled={savingKey === "confirmation_required"}
                    onChange={(event) => updateToggle("confirmation_required", event.target.checked)}
                  />
                </label>
                <label className="flex cursor-pointer items-center justify-between gap-4 rounded-md border border-border bg-background p-4">
                  <span>
                    <span className="block text-sm font-medium">Verbose replies</span>
                    <span className="mt-1 block text-sm text-muted-foreground">
                      CAP uses more detail when explaining reasoning and next steps.
                    </span>
                  </span>
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-primary"
                    checked={settings.verbose_replies}
                    disabled={savingKey === "verbose_replies"}
                    onChange={(event) => updateToggle("verbose_replies", event.target.checked)}
                  />
                </label>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
