import { AppShell } from "@/components/app-shell";
import { ColdStartBanner } from "@/components/cold-start-banner";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <ColdStartBanner />
      {children}
    </AppShell>
  );
}
