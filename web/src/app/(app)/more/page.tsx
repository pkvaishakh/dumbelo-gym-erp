"use client";
import {
  Building2, CalendarCheck, ClipboardList, Dumbbell, HandCoins, LifeBuoy, LogOut, QrCode, Receipt, Repeat, Tag, UserRound, Users, Wallet,
} from "lucide-react";
import { useState } from "react";

import { PageBar } from "@/components/shell";
import { Details, ErrorText, Field, Icon, MenuRow, Section, Sheet } from "@/components/ui";
import { phone, plural, rupees } from "@/lib/format";
import { useAction, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Collection, Summary } from "@/lib/types";

export default function MorePage() {
  const { me, role, signOut, switchGym } = useSession();
  const r = role.role;
  const label = { admin: "Admin", receptionist: "Receptionist", trainer: "Trainer", member: "Member" }[r];
  const summary = useGet<Summary>("/api/reports/summary/", undefined, r === "admin");
  const col = useGet<Collection>("/api/payments/collection/", undefined, r === "admin" || r === "receptionist");
  const [support, setSupport] = useState(false);
  return (
    <div className="rl-app rl-root">
      <PageBar title="More" sub={`${me.name} • ${label}`} />
      <main className="rl-app__main">
        {r === "admin" && (
          <Section title="Your gym">
            <ul className="rl-card rl-remind">
              <MenuRow icon={Users} title="Members" href="/members" value={summary.data ? plural(summary.data.members.total, "member") : undefined} />
              <MenuRow icon={Dumbbell} title="Trainers" href="/staff?role=trainer" />
              <MenuRow icon={UserRound} title="Receptionists" href="/staff?role=receptionist" />
              <MenuRow icon={ClipboardList} title="Tasks" href="/tasks" />
              <MenuRow icon={Receipt} title="Expenses" href="/expenses" value={summary.data ? `${rupees(summary.data.expenses_month_paise)} this month` : undefined} />
              <MenuRow icon={Wallet} title="Today’s collection" href="/collection" value={col.data ? rupees(col.data.total_paise) : undefined} />
              <MenuRow icon={Building2} title="Branches" href="/branches" value={role.branches.length} />
              <MenuRow icon={Tag} title="Plans and offers" href="/plans" />
              <MenuRow icon={LifeBuoy} title="Rackline support access" onClick={() => setSupport(true)} />
            </ul>
          </Section>
        )}
        {r === "receptionist" && (
          <Section title="Front desk">
            <ul className="rl-card rl-remind">
              <MenuRow icon={Wallet} title="Today’s collection" href="/collection" value={col.data ? rupees(col.data.total_paise) : undefined} />
              <MenuRow icon={HandCoins} title="Payment due" href="/members?status=due" />
              <MenuRow icon={CalendarCheck} title="Expiring this week" href="/members?status=expiring" />
              <MenuRow icon={ClipboardList} title="My Tasks" href="/tasks" />
              <MenuRow icon={Tag} title="Plans and offers" href="/plans" />
            </ul>
          </Section>
        )}
        {r === "trainer" && (
          <Section title="Your work">
            <ul className="rl-card rl-remind">
              <MenuRow icon={Users} title="My Members" href="/members" />
              <MenuRow icon={ClipboardList} title="My Tasks" href="/tasks" />
              <MenuRow icon={QrCode} title="Check in with the wall QR" href="/checkin" />
            </ul>
          </Section>
        )}
        {r === "member" && (
          <Section title="Your membership">
            <ul className="rl-card rl-remind">
              <MenuRow icon={QrCode} title="Check In" href="/checkin" />
              <MenuRow icon={CalendarCheck} title="Visits" href="/visits" />
            </ul>
          </Section>
        )}
        <Section title="Account Details">
          <Details rows={[
            { icon: UserRound, label: "Name", value: me.name },
            ...(me.email ? [{ icon: UserRound, label: "Email", value: me.email }] : []),
            { icon: UserRound, label: "Mobile number", value: phone(me.phone) },
            { icon: Building2, label: "Gym", value: role.gym_name },
          ]} />
        </Section>
        <Section label="Sign out">
          <ul className="rl-card rl-remind">
            {me.roles.length > 1 && me.roles.filter((x) => x.gym !== role.gym).map((x) => (
              <MenuRow key={x.gym} icon={Repeat} title={`Switch to ${x.gym_name}`} onClick={() => switchGym(x.gym)} />
            ))}
            <li><button className="rl-remind__row" type="button" onClick={signOut}>
              <span className="rl-chipicon" aria-hidden="true"><Icon as={LogOut} size="sm" /></span>
              <span className="rl-remind__text"><span className="rl-row__title">Sign Out</span></span>
            </button></li>
          </ul>
        </Section>
      </main>
      {r === "admin" && <SupportSheet open={support} onClose={() => setSupport(false)} />}
    </div>
  );
}

function SupportSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const list = useGet<{ results: { id: number; starts: string; ends: string }[] }>("/api/support-access/", undefined, open);
  const [hours, setHours] = useState("4");
  const a = useAction();
  const active = (list.data?.results ?? []).find((w) => new Date(w.ends) > new Date());
  async function grant() { try { await a.run("/api/support-access/", { hours: Number(hours) }, { refresh: ["/api/support-access/"] }); } catch { /* shown */ } }
  return (
    <Sheet open={open} onClose={onClose} title="Rackline support access">
      <p className="rl-row__meta">Rackline&apos;s team can only look inside your gym while you allow it. They can read but not change anything, and every look is recorded.</p>
      {active ? (
        <p className="rl-statusline">Support can look until {new Date(active.ends).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}.</p>
      ) : (
        <Field label="Allow for (hours)">{(id) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={1} max={72} value={hours} onChange={(e) => setHours(e.target.value)} />}</Field>
      )}
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        {!active && <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={grant}>Allow Support</button>}
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Close</button>
      </div>
    </Sheet>
  );
}
