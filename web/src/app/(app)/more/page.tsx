"use client";
import {
  Banknote, BadgeIndianRupee, Building2, Calculator, CalendarCheck, CalendarClock, ClipboardList, Dumbbell, KeyRound, Landmark, LifeBuoy, LogOut, MessageCircle, Pencil, QrCode, Receipt, Repeat, ScanLine, ShieldCheck, SlidersHorizontal, Tag, UserRound, Users, Wallet,
} from "lucide-react";
import { useState } from "react";

import { useAccountsOverviewRetrieve } from "@/api/gen/accounts/accounts";
import { useCashList } from "@/api/gen/cash/cash";
import { useExpensesTodayRetrieve } from "@/api/gen/expenses/expenses";
import { PageBar } from "@/components/shell";
import { Details, Icon, MenuRow, Section } from "@/components/ui";
import { AccountSheet, PasswordSheet } from "@/features/account";
import { PausedNotice } from "@/features/paused";
import { phone, plural, rupees } from "@/lib/format";
import { useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Collection, Summary } from "@/lib/types";

export default function MorePage() {
  const { me, role, paused, signOut, switchGym } = useSession();
  const r = role.role;
  const admin = r === "admin" && !paused; // a paused gym's admin reaches More only, and the gym's figures stay shut
  const desk = r === "receptionist";
  const label = { admin: "Admin", receptionist: "Receptionist", trainer: "Trainer", member: "Member" }[r];
  const summary = useGet<Summary>("/api/reports/summary/", undefined, admin);
  const col = useGet<Collection>("/api/payments/collection/", undefined, admin || desk);
  const spent = useExpensesTodayRetrieve(undefined, { query: { enabled: desk } }).data?.data;
  const funds = useAccountsOverviewRetrieve({ query: { enabled: admin } }).data?.data.totals;
  const drawers = useCashList(undefined, { query: { enabled: desk } }).data?.data;
  const cashIn = drawers?.filter((d) => d.balance_paise !== null).reduce((t, d) => t + (d.balance_paise ?? 0), 0);
  const [sheet, setSheet] = useState<"details" | "password" | null>(null);
  const staff = r !== "member"; // a member's details are changed by the desk
  return (
    <div className="rl-app rl-root">
      <PageBar title="More" sub={`${me.name} • ${label}`} />
      <main className="rl-app__main">
        {r === "admin" && paused && (
          <Section title="Your gym">
            <PausedNotice />
            <ul className="rl-card rl-remind" style={{ marginTop: "var(--space-3)" }}><MenuRow icon={BadgeIndianRupee} title="Dumbelo plan" href="/dumbelo-plan" /></ul>
          </Section>
        )}
        {admin && (
          <>
            <Section title="Members and staff">
              <ul className="rl-card rl-remind">
                <MenuRow icon={CalendarCheck} title="Attendance" href="/attendance" value={summary.data ? `${plural(summary.data.checkins.total, "check-in")} today` : undefined} />
                <MenuRow icon={Dumbbell} title="Trainers" href="/staff?role=trainer" />
                <MenuRow icon={UserRound} title="Receptionists" href="/staff?role=receptionist" />
                <MenuRow icon={ClipboardList} title="Tasks" href="/tasks" />
              </ul>
            </Section>
            <Section title="Money">
              <ul className="rl-card rl-remind">
                <MenuRow icon={Wallet} title="Payments" href="/collection" value={col.data ? rupees(col.data.total_paise) : undefined} />
                <MenuRow icon={Receipt} title="Expenses" href="/expenses" value={summary.data ? `${rupees(summary.data.expenses_month_paise)} this month` : undefined} />
                <MenuRow icon={CalendarClock} title="Dues" href="/expenses/dues" value={summary.data ? (summary.data.expense_dues.count ? `${rupees(summary.data.expense_dues.total_paise)} to pay` : "All paid") : undefined} />
                <MenuRow icon={Banknote} title="Payroll" href="/payroll" />
                <MenuRow icon={Landmark} title="Cash and bank" href="/money" value={funds ? rupees(funds.total_paise) : undefined} />
              </ul>
            </Section>
            <Section title="Gym setup">
              <ul className="rl-card rl-remind">
                <MenuRow icon={Building2} title="Branches" href="/branches" value={role.branches.length} />
                <MenuRow icon={Tag} title="Plans and offers" href="/plans" />
                <MenuRow icon={ScanLine} title="Devices" href="/devices" />
                <MenuRow icon={MessageCircle} title="Messages" href="/messages" />
                <MenuRow icon={SlidersHorizontal} title="Settings" href="/settings" />
              </ul>
            </Section>
            <Section title="Your Dumbelo account">
              <ul className="rl-card rl-remind">
                <MenuRow icon={BadgeIndianRupee} title="Dumbelo plan" href="/dumbelo-plan" />
                <MenuRow icon={LifeBuoy} title="Support access" href="/support" />
              </ul>
            </Section>
          </>
        )}
        {r === "receptionist" && (
          <Section title="Front desk">
            <ul className="rl-card rl-remind">
              <MenuRow icon={Wallet} title="Payments" href="/collection" value={col.data ? rupees(col.data.total_paise) : undefined} />
              <MenuRow icon={Receipt} title="Expenses" href="/expenses" value={spent ? `${rupees(spent.total_paise)} today` : undefined} />
              <MenuRow icon={Calculator} title="Cash in hand" href="/cash" value={cashIn !== undefined ? rupees(cashIn) : undefined} />
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
          {staff && (
            <ul className="rl-card rl-remind" style={{ marginTop: "var(--space-3)" }}>
              <MenuRow icon={Pencil} title="Edit Details" onClick={() => setSheet("details")} />
              <MenuRow icon={KeyRound} title="Change Password" onClick={() => setSheet("password")} />
            </ul>
          )}
        </Section>
        {me.is_dumbelo_admin && (
          <Section title="Dumbelo">
            <ul className="rl-card rl-remind"><MenuRow icon={ShieldCheck} title="Dumbelo Console" href="/console" /></ul>
          </Section>
        )}
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
      {staff && <AccountSheet open={sheet === "details"} onClose={() => setSheet(null)} />}
      {staff && <PasswordSheet open={sheet === "password"} onClose={() => setSheet(null)} />}
    </div>
  );
}
