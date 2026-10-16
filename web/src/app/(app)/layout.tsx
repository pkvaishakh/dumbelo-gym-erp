"use client";
import { TabBar } from "@/components/shell";
import { SessionProvider } from "@/lib/session";

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

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider fallback={<Loading />}>
      {children}
      <TabBar />
    </SessionProvider>
  );
}
