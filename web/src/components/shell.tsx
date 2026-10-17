"use client";
/* App frame: headers, bottom navigation per role, the create sheet and the branch switcher. */
import {
  ArrowLeft, BarChart3, Building2, CalendarCheck, ChevronDown, ClipboardCheck, ClipboardList, Home, LayoutGrid, ListChecks,
  Plus, QrCode, Receipt, Repeat, Ticket, UserPlus, Users, Wallet, X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { greeting } from "@/lib/format";
import { useSession, type RoleName } from "@/lib/session";
import { CheckInSheet } from "@/features/checkin";

import { Icon, Mark, Sheet } from "./ui";

function Avatar() {
  const { me } = useSession();
  return <Link className="rl-avatar rl-pressable" href="/more" aria-label={`Profile: ${me.name}`}>{me.initials}</Link>;
}

/** The greeting at the top of a home screen, with the admin's branch switcher. Goes first inside <main>. */
export function Greeting() {
  const { me, role, branchName } = useSession();
  return (
    <div className="rl-greeting">
      <h1 className="rl-greeting__hello">{greeting(me.name, true)}</h1>
      {role.role === "admin" ? <BranchChip /> : (
        <p className="rl-appbar__branch" style={{ margin: 0 }}>{branchName}{role.role !== "member" ? (role.branches.length > 1 ? " branches" : " branch") : ""}</p>
      )}
    </div>
  );
}

/** The admin's branch switcher: a chip naming the branch, opening the branch sheet. */
export function BranchChip() {
  const { branchName } = useSession();
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="rl-chip" type="button" onClick={() => setOpen(true)} aria-haspopup="dialog" aria-label={`Branch: ${branchName}. Switch branch`}>
        {branchName}<Icon as={ChevronDown} size="xs" />
      </button>
      <BranchSheet open={open} onClose={() => setOpen(false)} />
    </>
  );
}

/** The home header: logo and avatar. */
export function HomeBar() {
  return (
    <>
      <header className="rl-appbar"><div className="rl-appbar__in">
        <Link className="rl-logo" href="/home" aria-label="Rackline home"><Mark /></Link>
        <div className="rl-appbar__spacer" />
        <Avatar />
      </div></header>
    </>
  );
}

export function BranchSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { role, branch, setBranch } = useSession();
  const pick = (id: number | null) => { setBranch(id); onClose(); };
  return (
    <Sheet open={open} onClose={onClose} title="Branch">
      <ul className="rl-sheet__list">
        <li><button className="rl-sheet__item" type="button" aria-pressed={branch === null} onClick={() => pick(null)}>
          <span className="rl-chipicon"><Icon as={LayoutGrid} size="sm" /></span><span className="rl-sheet__text">All branches</span>{branch === null && <span className="rl-tag rl-tag--now">Now</span>}
        </button></li>
        {role.branches.map((b) => (
          <li key={b.id}><button className="rl-sheet__item" type="button" aria-pressed={branch === b.id} onClick={() => pick(b.id)}>
            <span className="rl-chipicon"><Icon as={Building2} size="sm" /></span><span className="rl-sheet__text">{b.name}</span>{branch === b.id && <span className="rl-tag rl-tag--now">Now</span>}
          </button></li>
        ))}
      </ul>
    </Sheet>
  );
}

/** A tab screen's header: title, a line under it, and the avatar or an `action` in its place (Reports' branch chip). */
export function PageBar({ title, sub, back, action }: { title: string; sub?: React.ReactNode; back?: string | true; action?: React.ReactNode }) {
  const router = useRouter();
  return (
    <header className="rl-appbar rl-appbar--scroll"><div className="rl-appbar__in">
      {back && (
        <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Back" onClick={() => (back === true ? router.back() : router.push(back))}>
          <Icon as={ArrowLeft} />
        </button>
      )}
      <div className="rl-appbar__who"><h1 className="rl-pagetitle">{title}</h1>{sub && <p className="rl-appbar__branch">{sub}</p>}</div>
      {action ?? (!back && <Avatar />)}
    </div></header>
  );
}

/** A record's header: back arrow and title. */
export function DetailBar({ title, back, action }: { title: string; back?: string; action?: React.ReactNode }) {
  const router = useRouter();
  return (
    <header className="rl-appbar"><div className="rl-appbar__in">
      <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Back" onClick={() => (back ? router.push(back) : router.back())}><Icon as={ArrowLeft} /></button>
      <h1 className="rl-topbar__title">{title}</h1>
      {action ?? <span style={{ width: 44 }} />}
    </div></header>
  );
}

/** A task screen's header: close, title, step. */
export function TaskBar({ title, aside, onClose, step }: { title: string; aside?: string; onClose?: () => void; step?: [number, number] }) {
  const router = useRouter();
  return (
    <>
      <header className="rl-appbar"><div className="rl-appbar__in">
        <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Close" onClick={onClose ?? (() => router.back())}><Icon as={X} /></button>
        <h1 className="rl-topbar__title">{title}</h1>
        <p className="rl-topbar__aside">{step ? `Step ${step[0]} of ${step[1]}` : aside}</p>
      </div></header>
      {step && (
        <div className="rl-steps" style={{ padding: "0 var(--space-4)" }}>
          <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: step[0] / step[1] }} /></span>
        </div>
      )}
    </>
  );
}

type Tab = { href: string; label: string; icon: typeof Home };
const TABS: Record<RoleName, Tab[]> = {
  admin: [
    { href: "/home", label: "Home", icon: Home },
    { href: "/attendance", label: "Attendance", icon: CalendarCheck },
    { href: "/reports", label: "Reports", icon: BarChart3 },
    { href: "/more", label: "More", icon: LayoutGrid },
  ],
  receptionist: [
    { href: "/home", label: "Home", icon: Home },
    { href: "/members", label: "Members", icon: Users },
    { href: "/attendance", label: "Attendance", icon: CalendarCheck },
    { href: "/more", label: "More", icon: LayoutGrid },
  ],
  trainer: [
    { href: "/home", label: "Home", icon: Home },
    { href: "/members", label: "My Members", icon: Users },
    { href: "/tasks", label: "My Tasks", icon: ListChecks },
    { href: "/more", label: "More", icon: LayoutGrid },
  ],
  member: [
    { href: "/home", label: "Home", icon: Home },
    { href: "/checkin", label: "Check In", icon: QrCode },
    { href: "/visits", label: "Visits", icon: CalendarCheck },
    { href: "/more", label: "More", icon: LayoutGrid },
  ],
};

export function TabBar() {
  const { role } = useSession();
  const path = usePathname();
  const [create, setCreate] = useState(false);
  const [checking, setChecking] = useState(false);
  const tabs = TABS[role.role];
  if (/\/(new|edit)(\/|$)/.test(path)) return null; // task screens have their own action bar
  const hasCreate = role.role === "admin" || role.role === "receptionist";
  const current = (href: string) => path === href || (href !== "/home" && path.startsWith(href + "/")) || (href === "/more" && /^\/(staff|plans|offers|branches|devices|expenses|payroll|support|tasks)/.test(path) && role.role === "admin") || (href === "/more" && path.startsWith("/expenses") && role.role === "receptionist") || (href === "/more" && path.startsWith("/members") && role.role === "admin");
  const render = (t: Tab) => (
    <Link key={t.href} className="rl-tab" href={t.href} aria-current={current(t.href) ? "page" : undefined}>
      <span className="rl-tab__icon"><Icon as={t.icon} /></span>{t.label}
    </Link>
  );
  return (
    <div className="rl-root">
      <nav className="rl-tabbar" aria-label="Main"><div className="rl-tabbar__in">
        {tabs.slice(0, 2).map(render)}
        {hasCreate && (
          <button className="rl-fab" type="button" aria-haspopup="dialog" aria-expanded={create} aria-label="Create" onClick={() => setCreate(true)}>
            <Icon as={Plus} />
          </button>
        )}
        {tabs.slice(2).map(render)}
      </div></nav>
      {hasCreate && <CreateSheet open={create} onClose={() => setCreate(false)} onCheckIn={() => { setCreate(false); setChecking(true); }} />}
      {hasCreate && <CheckInSheet open={checking} onClose={() => setChecking(false)} />}
    </div>
  );
}

function CreateSheet({ open, onClose, onCheckIn }: { open: boolean; onClose: () => void; onCheckIn: () => void }) {
  const { role } = useSession();
  const router = useRouter();
  const go = (href: string) => { onClose(); router.push(href); };
  const item = (label: string, icon: typeof Home, href: string | (() => void)) => (
    <li key={label}><button className="rl-sheet__item" type="button" onClick={() => typeof href === "string" ? go(href) : href()}>
      <span className="rl-chipicon"><Icon as={icon} size="sm" /></span><span className="rl-sheet__text">{label}</span>
    </button></li>
  );
  return (
    <Sheet open={open} onClose={onClose} title="Create">
      <p className="rl-sheet__label" style={{ marginTop: "var(--space-1)" }}>Members</p>
      <ul className="rl-sheet__list">
        {item("Add Member", UserPlus, "/members/new")}
        {item("New Subscription", Ticket, "/subscriptions/new")}
        {item("Collect Payment", Wallet, "/payments/new")}
        {item("Mark Attendance", ClipboardCheck, onCheckIn)}
      </ul>
      {role.role === "admin" && (
        <>
          <p className="rl-sheet__label">Staff and expenses</p>
          <ul className="rl-sheet__list">
            {item("Add Trainer", UserPlus, "/staff/new?role=trainer")}
            {item("Add Receptionist", UserPlus, "/staff/new?role=receptionist")}
            {item("Assign Task", ClipboardList, "/tasks?new=1")}
            {item("Add Expense", Receipt, "/expenses/new")}
            {item("Add Recurring Expense", Repeat, "/expenses/recurring/new")}
          </ul>
        </>
      )}
      {role.role === "receptionist" && (
        <>
          <p className="rl-sheet__label">Expenses</p>
          <ul className="rl-sheet__list">{item("Add Expense", Receipt, "/expenses/new")}</ul>
        </>
      )}
    </Sheet>
  );
}
