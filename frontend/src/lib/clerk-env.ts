const CLERK_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() ?? "";
const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY?.trim() ?? "";

export const clerkPublishableKey = CLERK_PUBLISHABLE_KEY;
export const clerkSecretKey = CLERK_SECRET_KEY;

export function isClerkConfigured(): boolean {
  return Boolean(CLERK_PUBLISHABLE_KEY && CLERK_SECRET_KEY);
}

export function assertClerkBuildConfig(): void {
  const missing: string[] = [];

  if (!CLERK_PUBLISHABLE_KEY) {
    missing.push("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY");
  }
  if (!CLERK_SECRET_KEY) {
    missing.push("CLERK_SECRET_KEY");
  }

  if (missing.length === 0) {
    return;
  }

  throw new Error(
    [
      "Clerk authentication is not configured for production build.",
      "",
      `Missing environment variable(s): ${missing.join(", ")}`,
      "",
      "Add them to frontend/.env.local (local) or your deployment platform (production).",
      "Copy frontend/.env.example for the full list of required variables.",
      "Get keys from: https://dashboard.clerk.com/last-active?path=api-keys",
    ].join("\n")
  );
}
