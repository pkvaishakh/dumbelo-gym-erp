"use client";
import { ConsoleTabBar } from "@/components/shell";
import { SkeletonRows } from "@/components/ui";
import { ConsoleProvider } from "@/lib/session";

function Loading() {
  return (
    <div className="rl-app rl-root" aria-busy="true">
      <div className="rl-app__main" style={{ padding: "var(--space-4)" }}>
        <span className="rl-skel" style={{ height: 32, width: "50%", marginTop: 24, marginBottom: 24 }} />
        <SkeletonRows />
      </div>
    </div>
  );
}

/** The Console: Rackline's own side, for Rackline admins. The same shell and design system as the gym app. */
export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return (
    <ConsoleProvider fallback={<Loading />}>
      {children}
      <ConsoleTabBar />
    </ConsoleProvider>
  );
}
