"use client";
/* What a suspended gym's people see. The API refuses every gym call with gym_suspended; its admins can still open More. */
import Link from "next/link";

import { useSession } from "@/lib/session";

const WHO_TO_ASK: Record<string, string> = {
  admin: "Your staff and members can't use the app while it's paused. Contact Rackline to turn it back on.",
  member: "You can't check in or see your membership in the app for now. Ask at the front desk.",
};

export function PausedScreen() {
  const { me, role, signOut, switchGym } = useSession();
  const admin = role.role === "admin";
  const others = me.roles.filter((r) => r.gym !== role.gym);
  return (
    <div className="rl-root" style={{ padding: 24 }}>
      <h1 className="rl-display">{role.gym_name} is paused</h1>
      <p className="rl-lede">{admin ? "Your gym's Rackline account is paused." : "The app is paused for this gym."}</p>
      <p className="rl-row__meta">{WHO_TO_ASK[role.role] ?? "You can't use the app here for now. Ask your gym's admin."}</p>
      <div className="rl-sheet__actions" style={{ marginTop: 24 }}>
        {admin && <Link className="rl-button rl-button--block" href="/more">Open More</Link>}
        {others.map((r) => (
          <button key={r.gym} className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => switchGym(r.gym)}>Switch to {r.gym_name}</button>
        ))}
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={signOut}>Sign Out</button>
      </div>
    </div>
  );
}

/** On More, in place of the gym's sections, for an admin of a paused gym. */
export function PausedNotice() {
  return (
    <div className="rl-card rl-card--pad">
      <p className="rl-row__title" style={{ margin: 0 }}>Your gym&apos;s Rackline account is paused</p>
      <p className="rl-row__meta" style={{ marginBottom: 0 }}>{WHO_TO_ASK.admin}</p>
    </div>
  );
}
