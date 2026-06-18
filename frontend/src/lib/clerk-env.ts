const CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() ?? "";
const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY?.trim() ?? "";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "";
const PLACEHOLDER_VALUES = new Set(["<Render Secret>"]);

export const clerkPublishableKey = CLERK_PUBLISHABLE_KEY;
export const clerkSecretKey = CLERK_SECRET_KEY;
export const apiBaseUrl = API_BASE_URL;

export function isClerkConfigured(): boolean {
  return Boolean(CLERK_PUBLISHABLE_KEY && CLERK_SECRET_KEY);
}

export function assertClerkBuildConfig(): void {
  const missing: string[] = [];
  const placeholders: string[] = [];

  function requireEnv(name: string, value: string): void {
    if (!value) {
      missing.push(name);
      return;
    }
    if (PLACEHOLDER_VALUES.has(value)) {
      placeholders.push(name);
    }
  }

  requireEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", CLERK_PUBLISHABLE_KEY);
  requireEnv("CLERK_SECRET_KEY", CLERK_SECRET_KEY);
  requireEnv("NEXT_PUBLIC_API_BASE_URL", API_BASE_URL);

  if (missing.length === 0 && placeholders.length === 0) {
    return;
  }

  throw new Error(
    [
      "Frontend environment is not configured for production build.",
      "",
      missing.length > 0 ? `Missing environment variable(s): ${missing.join(", ")}` : null,
      placeholders.length > 0 ? `Placeholder environment variable(s): ${placeholders.join(", ")}` : null,
      "",
      "Add them to frontend/.env.local (local) or your deployment platform (production).",
      "Copy frontend/.env.example for the full list of required variables.",
      "Get keys from: https://dashboard.clerk.com/last-active?path=api-keys",
    ].filter(Boolean).join("\n")
  );
}
