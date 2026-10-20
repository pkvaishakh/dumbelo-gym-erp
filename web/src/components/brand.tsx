/* The design system's pieces that are only markup: an icon, the logo mark and the barbell. No hooks and no
 * "use client", so server components (the landing page) can render them too; ui.tsx re-exports them for the app. */
import type { LucideIcon } from "lucide-react";

export function Icon({ as: C, size }: { as: LucideIcon; size?: "sm" | "xs" }) {
  return <C className={`rl-icon${size ? ` rl-icon--${size}` : ""}`} strokeWidth={1.75} aria-hidden="true" />;
}

export function Mark({ className = "rl-logo__mark" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" aria-hidden="true">
      <rect className="rl-logo__tile" width="40" height="40" rx="12" />
      <rect className="rl-logo__plate" x="9.5" y="15" width="5" height="10" rx="2.5" />
      <rect className="rl-logo__plate" x="17.5" y="12" width="5" height="16" rx="2.5" />
      <rect className="rl-logo__plate" x="25.5" y="9" width="5" height="22" rx="2.5" />
    </svg>
  );
}

export function Barbell({ onInk, load }: { onInk?: boolean; load?: boolean }) {
  return (
    <div className={`rl-barbell rl-barbell--bleed${onInk ? " rl-barbell--on-ink" : ""}${load ? " rl-barbell--load" : ""}`} aria-hidden="true">
      <span className="rl-barbell__tip" /><span className="rl-plate rl-plate--sm" /><span className="rl-plate rl-plate--md" />
      <span className="rl-plate rl-plate--lg" /><span className="rl-plate" /><span className="rl-plate rl-plate--volt" />
      <span className="rl-barbell__collar" /><span className="rl-barbell__shaft" />
    </div>
  );
}
