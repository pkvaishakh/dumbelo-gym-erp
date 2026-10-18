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

/** A suspended gym shows its paused screen everywhere, except More for its admins (the API keeps the rest shut). */
function Frame({ children }: { children: React.ReactNode }) {
  const { role, paused } = useSession();
  const path = usePathname();
  if (!paused) return <>{children}<TabBar /></>;
  return role.role === "admin" && path === "/more" ? <>{children}</> : <PausedScreen />;
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider fallback={<Loading />}>
      <Frame>{children}</Frame>
    </SessionProvider>
  );
}
