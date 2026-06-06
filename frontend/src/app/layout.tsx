import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";

import "./globals.css";
import { clerkPublishableKey } from "@/lib/clerk-env";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "CAP - Context-Aware Partner",
  description: "A context-aware AI partner for better decisions."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <ClerkProvider publishableKey={clerkPublishableKey}>{children}</ClerkProvider>
      </body>
    </html>
  );
}
