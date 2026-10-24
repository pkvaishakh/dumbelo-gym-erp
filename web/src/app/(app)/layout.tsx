"use client";
import { usePathname } from "next/navigation";

import { TabBar } from "@/components/shell";
import { PausedScreen } from "@/features/paused";
import { SessionProvider, useSession } from "@/lib/session";

function Loading() {
  return (
    <div className="rl-app rl-root" aria-busy="true">
      <div className="rl-app__main" style={{ padding: "var(--space-4)" }}>
        <span className="rl-skel" style={{ height: 32, width: "60%", marginTop: 24 }} />
        <span className="rl-skel" style={{ height: 120, marginTop: 24 }} />
        <span className="rl-skel" style={{ height: 200, marginTop: 16 }} />
      </div>
    </div>
  );
}

// What a suspended gym's admins can still open: More, and their Dumbelo plan (the API keeps the rest shut).
const OPEN_WHEN_PAUSED = ["/more", "/dumbelo-plan"];

/** A suspended gym shows its paused screen everywhere, except OPEN_WHEN_PAUSED for its admins. */
function Frame({ children }: { children: React.ReactNode }) {
  const { role, paused } = useSession();
  const path = usePathname();
  if (!paused) return <>{children}<TabBar /></>;
  const open = OPEN_WHEN_PAUSED.some((p) => path === p || path.startsWith(`${p}/`)); // the plan's invoices and receipts too
  return role.role === "admin" && open ? <>{children}</> : <PausedScreen />;
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="rl-statusbar" aria-hidden />
      <SessionProvider fallback={<Loading />}>
        <Frame>{children}</Frame>
      </SessionProvider>
    </>
  );
}
