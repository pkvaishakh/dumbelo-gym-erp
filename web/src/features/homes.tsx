"use client";
import {
  AlertTriangle, Banknote, CalendarCheck, CalendarX, Check, ChevronRight, CircleCheck, ClipboardCheck, HandCoins, IndianRupee, ListChecks, QrCode, Receipt, ReceiptText, ScanLine,
  Ticket, UserPlus, Users, Wallet, type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useBranchesList } from "@/api/gen/branches/branches";
import { useCashList } from "@/api/gen/cash/cash";
import { useCheckinsList } from "@/api/gen/checkins/checkins";
import { useExpensesTodayRetrieve } from "@/api/gen/expenses/expenses";
import { useMembersList, useMembersTodayRetrieve } from "@/api/gen/members/members";
import type { TrainerToday } from "@/api/gen/model";
import { useStaffList } from "@/api/gen/staff/staff";
import { useTasksList } from "@/api/gen/tasks/tasks";
import { Greeting, HomeBar } from "@/components/shell";
import { Bar, Icon, PassActions, Photo, Section, SkeletonRows, Status, TaskStatus } from "@/components/ui";
import { day, gymToday, isoDate, planDays, plural, rupees, span } from "@/lib/format";
import { useGet } from "@/lib/hooks";
import { ptState, sessionsUsed } from "@/lib/pt";
import { useSession } from "@/lib/session";
import type { BranchDay, CheckinSummary, Collection, MemberSelf, Page, SessionCounts, Summary, TaskCounts, TrainerMember } from "@/lib/types";

import { CheckInSheet } from "./checkin";
import { MyPlansRows } from "./coach-plans";

export type AttentionRow = { count: number; title: string; meta: string; href: string; dot?: "" | "ring" | "ink" | "muted" };

/** The Needs attention card. With four rows it carries the design's dots: filled for today, a ring for this week,
 *  ink for money; the label always says it too. */
export function Attention({ rows }: { rows: AttentionRow[] }) {
  const shown = rows.filter((r) => r.count > 0);
  if (!shown.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Nothing needs you right now.</p></div>;
  const dots = shown.length >= 4;
  return (
    <ul className={`rl-attn${dots ? " rl-attn--dots" : ""}`}>
      {shown.map((r) => (
        <li key={r.title}><Link className="rl-attn__row" href={r.href}>
          <span className="rl-attn__count">{r.count}</span>
          {dots && r.dot !== undefined && <span className={`rl-attn__dot${r.dot ? ` rl-attn__dot--${r.dot}` : ""}`} aria-hidden="true" />}
          <span className="rl-attn__text"><span className="rl-row__title">{r.title}</span><span className="rl-row__meta">{r.meta}</span></span>
          <ChevronRight className="rl-icon rl-icon--sm rl-attn__chev" strokeWidth={1.75} aria-hidden />
        </Link></li>
      ))}
    </ul>
  );
}

/** "₹1,20,000 to pay • 1 bill late": what the gym owes in bills and salaries, the late part first to the eye. */
function expenseDuesMeta(d: Summary["expense_dues"]) {
  const parts = [`${rupees(d.total_paise)} to pay`];
  if (d.overdue_bills) parts.push(`${plural(d.overdue_bills, "bill")} late`);
  else if (d.salaries) parts.push(plural(d.salaries, "salary", "salaries"));
  return parts.join(" • ");
}

/** Check-ins by session: members, trainers and receptionists, as on the Attendance tab. */
export function SessionsTable({ sessions, staff }: { sessions: SessionCounts[]; staff?: { trainer: number; receptionist: number } }) {
  const { branch } = useSession();
  const branches = useBranchesList();
  const hours = useMemo(() => {
    const map = new Map<string, string>();
    const list = branches.data?.data.results ?? [];
    for (const b of list.filter((b) => !branch || b.id === branch)) for (const s of b.sessions) if (!map.has(s.name)) map.set(s.name, span(s.starts, s.ends));
    return map;
  }, [branches.data, branch]);
  const names = [...new Set([...hours.keys(), ...sessions.map((s) => s.session)])];
  const byName = new Map(sessions.map((s) => [s.session, s]));
  const total = (k: keyof Omit<SessionCounts, "session">) => sessions.reduce((n, s) => n + s[k], 0);
  const rows: { key: keyof Omit<SessionCounts, "session">; title: string; meta: string; href: string }[] = [
    { key: "member", title: "Members", meta: `${total("member")} so far`, href: "/attendance" },
    { key: "trainer", title: "Trainers", meta: staff ? `${total("trainer")} of ${staff.trainer} checked in` : `${total("trainer")} checked in`, href: "/attendance?who=staff" },
    { key: "receptionist", title: "Receptionists", meta: staff ? `${total("receptionist")} of ${staff.receptionist} checked in` : `${total("receptionist")} checked in`, href: "/attendance?who=staff" },
  ];
  return (
    <div className="rl-card rl-shifts" style={{ ["--n" as string]: names.length }}>
      <div className="rl-shifts__head" aria-hidden="true">
        <span />
        {names.map((n) => <span className="rl-shifts__h" key={n}>{n}<small>{hours.get(n) ?? ""}</small></span>)}
      </div>
      <ul className="rl-shifts__list">
        {rows.map((r) => (
          <li key={r.key}><Link className="rl-shifts__row" href={r.href} aria-label={`${r.title}: ${names.map((n) => `${n} ${byName.get(n)?.[r.key] ?? 0}`).join(", ")}. ${r.meta}`}>
            <span className="rl-shifts__who"><span className="rl-row__title">{r.title}</span><span className="rl-row__meta">{r.meta}</span></span>
            {names.map((n) => { const v = byName.get(n)?.[r.key] ?? 0; return <span className={`rl-shifts__n${v ? "" : " is-zero"}`} key={n}>{v}</span>; })}
          </Link></li>
        ))}
      </ul>
    </div>
  );
}

function useStaffCounts() {
  const { branch } = useSession();
  const staff = useStaffList({ is_active: true, limit: 100, ...(branch ? { branches: [branch] } : {}) });  // a branch's staff fit one page
  const list = staff.data?.data.results ?? [];
  return { trainer: list.filter((s) => s.role === "trainer").length, receptionist: list.filter((s) => s.role === "receptionist").length };
}

function MyTasks({ limit = 3 }: { limit?: number }) {
  const tasks = useTasksList({ state: "open", limit });
  const open = tasks.data?.data.results ?? [];
  const total = tasks.data?.data.count ?? 0;
  if (tasks.isLoading) return <SkeletonRows n={2} />;
  if (!open.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No open tasks. You&apos;re all caught up.</p></div>;
  return (
    <>
      <ul className="rl-card rl-mlist rl-mlist--compact">
        {open.slice(0, limit).map((t) => (
          <li key={t.id}><Link className="rl-mrow rl-tkrow" href={`/tasks?open=${t.id}`}>
            <span className="rl-chipicon" aria-hidden="true"><Icon as={ListChecks} size="sm" /></span>
            <span className="rl-row__title rl-mrow__name">{t.title}</span>
            <span className="rl-row__meta rl-mrow__meta">Due {day(t.due_date)}</span>
            <TaskStatus status={t.status} overdue={t.is_overdue} />
          </Link></li>
        ))}
      </ul>
      {total > limit && <p className="rl-listmore"><Link className="rl-link" href="/tasks"><span>See all {total}</span></Link></p>}
    </>
  );
}

/** Today at a glance, in two groups that fit one phone screen: money (dark card) and members. */
function Glance({ sum }: { sum: Summary }) {
  const active = sum.members.active + sum.members.expiring + sum.members.due;
  return (
    <div className="rl-glance">
      <div className="rl-glance__money">
        <Link className="rl-glance__hero rl-pressable" href="/reports">
          <span className="rl-glance__head">
            <span className="rl-glance__chip" aria-hidden="true"><Icon as={IndianRupee} size="sm" /></span>
            <span className="rl-glance__kicker">Today’s revenue</span>
            <ChevronRight className="rl-icon rl-icon--sm rl-glance__chev" strokeWidth={1.75} aria-hidden />
          </span>
          <span className="rl-glance__big">{rupees(sum.revenue.today_paise)}</span>
          <span className="rl-glance__note">{rupees(sum.revenue.month_paise)} this month</span>
        </Link>
        <div className="rl-glance__pair">
          <Link className="rl-glance__cell rl-pressable" href="/expenses">
            <span className="rl-glance__label"><Icon as={Receipt} size="sm" />Expenses today</span>
            <span className="rl-glance__value">{rupees(sum.expenses_today_paise)}</span>
            <span className="rl-glance__note">{rupees(sum.expenses_month_paise)} this month</span>
          </Link>
          <Link className="rl-glance__cell rl-pressable" href="/members?status=due">
            <span className="rl-glance__label"><Icon as={HandCoins} size="sm" />Outstanding dues</span>
            <span className="rl-glance__value">{rupees(sum.dues.total_paise)}</span>
            <span className="rl-glance__note">From {plural(sum.dues.members, "member")}</span>
          </Link>
        </div>
      </div>
      <div className="rl-glance__people">
        <Link className="rl-glance__cell rl-pressable" href="/members?status=active">
          <span className="rl-glance__label"><Icon as={Users} size="sm" />Active</span>
          <span className="rl-glance__value">{active.toLocaleString("en-IN")}</span>
          <span className="rl-glance__note">{sum.members.frozen} frozen</span>
        </Link>
        <Link className="rl-glance__cell rl-pressable" href="/attendance">
          <span className="rl-glance__label"><Icon as={CalendarCheck} size="sm" />Check-ins</span>
          <span className="rl-glance__value">{sum.checkins.total.toLocaleString("en-IN")}</span>
          <span className="rl-glance__note">Today so far</span>
        </Link>
        <Link className="rl-glance__cell rl-pressable" href="/members?status=expired">
          <span className="rl-glance__label"><Icon as={CalendarX} size="sm" />Expired</span>
          <span className="rl-glance__value">{sum.members.expired.toLocaleString("en-IN")}</span>
          <span className="rl-glance__note">Not renewed yet</span>
        </Link>
      </div>
    </div>
  );
}

export function GlanceLoading() {
  const cell = (i: number) => <div className="rl-glance__cell" key={i}><span className="rl-skel" style={{ height: 12, width: "60%" }} /><span className="rl-skel" style={{ height: 22, width: "80%", marginTop: 8 }} /></div>;
  return (
    <div className="rl-glance" aria-hidden="true">
      <div className="rl-glance__money"><div className="rl-glance__hero"><span className="rl-skel" style={{ height: 32, width: "55%" }} /></div><div className="rl-glance__pair">{[0, 1].map(cell)}</div></div>
      <div className="rl-glance__people">{[0, 1, 2].map(cell)}</div>
    </div>
  );
}

/** All branches: each branch's day side by side. Tapping one switches Home to that branch. */
function BranchesToday({ rows }: { rows: BranchDay[] }) {
  const { setBranch } = useSession();
  const top = Math.max(1, ...rows.map((b) => b.revenue_today_paise));
  return (
    <ul className="rl-card rl-brday">
      {rows.map((b) => (
        <li key={b.id}><button className="rl-brday__row" type="button" onClick={() => setBranch(b.id)}
          aria-label={`${b.name}: ${rupees(b.revenue_today_paise)} revenue, ${rupees(b.expenses_today_paise)} expenses, ${b.checkins} check-ins, ${b.active_members} active members. Show this branch`}>
          <span className="rl-brday__top">
            <span className="rl-row__title">{b.name}</span>
            <ChevronRight className="rl-icon rl-icon--sm rl-attn__chev" strokeWidth={1.75} aria-hidden />
          </span>
          <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: b.revenue_today_paise / top }} /></span>
          <span className="rl-brday__nums" aria-hidden="true">
            <span><b>{rupees(b.revenue_today_paise)}</b><small>Revenue</small></span>
            <span><b>{rupees(b.expenses_today_paise)}</b><small>Expenses</small></span>
            <span><b>{b.checkins}</b><small>Check-ins</small></span>
            <span><b>{b.active_members}</b><small>Active</small></span>
          </span>
        </button></li>
      ))}
    </ul>
  );
}

export function AdminHome() {
  const { branch } = useSession();
  const s = useGet<Summary>("/api/reports/summary/", { branch });
  const tasks = useGet<TaskCounts>("/api/tasks/counts/");
  const staff = useStaffCounts();
  const sum = s.data;
  const late = tasks.data?.overdue ?? 0;
  const [checking, setChecking] = useState(false);
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <Section label="Today’s overview">
          {sum ? <Glance sum={sum} /> : <GlanceLoading />}
        </Section>
        <div className="rl-app__cols">
          <div className="rl-app__col">
            <Section title="Quick actions">
              <div className="rl-tiles">
                <Link className="rl-tile rl-tile--primary rl-pressable" href="/members/new"><Icon as={UserPlus} /><span>Add Member</span></Link>
                <Link className="rl-tile rl-tile--primary rl-pressable" href="/payments/new"><Icon as={Wallet} /><span>Collect Payment</span></Link>
                <Link className="rl-tile rl-pressable" href="/subscriptions/new"><Icon as={Ticket} /><span>New Subscription</span></Link>
                <button className="rl-tile rl-pressable" type="button" onClick={() => setChecking(true)} aria-haspopup="dialog"><Icon as={ClipboardCheck} /><span>Mark Attendance</span></button>
              </div>
            </Section>
            <Section title="Needs attention">
              {sum ? <Attention rows={[
                { count: sum.members.expiring, title: "Memberships expiring soon", meta: "In the next 7 days", href: "/members?status=expiring", dot: "ring" },
                { count: sum.dues.members, title: "Pending payments", meta: `${rupees(sum.dues.total_paise)} due`, href: "/members?status=due", dot: "ink" },
                { count: sum.expense_dues.count, title: "Expense dues", meta: expenseDuesMeta(sum.expense_dues), href: "/expenses/dues", dot: "ink" },
                { count: late, title: "Overdue tasks", meta: "Past their due time", href: "/tasks?filter=overdue", dot: "" },
              ]} /> : <SkeletonRows n={2} />}
            </Section>
          </div>
          <div className="rl-app__col">
            <Section title="Check-ins today" aside={<p className="rl-section__aside">By session</p>}>
              {sum ? <SessionsTable sessions={sum.checkins.sessions} staff={staff} /> : <SkeletonRows n={3} />}
            </Section>
          </div>
        </div>
        {!branch && (sum?.branches?.length ?? 0) > 1 && (
          <Section title="Branches today" aside={<p className="rl-section__aside">Tap one to see it alone</p>}>
            <BranchesToday rows={sum!.branches!} />
          </Section>
        )}
      </main>
      <CheckInSheet open={checking} onClose={() => setChecking(false)} />
    </div>
  );
}

/** The desk's day on one phone screen, no sideways scroll: money in and out on the ink card, then the four member
 *  counts in a 2 × 2 card. A count that needs the desk turns amber (red for expired). Each money figure opens that
 *  day's list. */
function DeskGlance() {
  const { branch } = useSession();
  const today = isoDate(new Date());
  const counts = useGet<CheckinSummary>("/api/checkins/summary/", { date: today, branch });
  const expiring = useGet<Page<unknown>>("/api/members/", { status: "expiring", limit: 1, branch });
  const due = useGet<Page<unknown>>("/api/members/", { status: "due", limit: 1, branch });
  const expired = useGet<Page<unknown>>("/api/members/", { status: "expired", limit: 1, branch });
  const col = useGet<Collection>("/api/payments/collection/", { branch });
  const spentQ = useExpensesTodayRetrieve(branch ? { branch } : undefined);
  const spent = spentQ.data?.data;
  const drawers = (useCashList().data?.data ?? []).filter((d) => d.balance_paise !== null);
  const sum = (k: "balance_paise" | "in_paise" | "out_paise") => drawers.reduce((t, d) => t + (d[k] ?? 0), 0);
  const people: { n?: number; label: string; note: string; icon: LucideIcon; href: string; tone?: "attention" | "danger" }[] = [
    { n: counts.data?.totals.member, label: "Check-ins today", note: "Members so far", icon: CalendarCheck, href: "/attendance" },
    { n: expiring.data?.count, label: "Expiring this week", note: "Renew before they go", icon: AlertTriangle, href: "/members?status=expiring", tone: "attention" },
    { n: due.data?.count, label: "Payment due", note: "Members with a balance", icon: HandCoins, href: "/members?status=due", tone: "attention" },
    { n: expired.data?.count, label: "Expired", note: "Not renewed yet", icon: CalendarX, href: "/members?status=expired", tone: "danger" },
  ];
  return (
    <div className="rl-glance rl-glance--desk">
      <div className="rl-glance__money">
        {drawers.length > 0 && (
          <Link className="rl-glance__hero rl-pressable" href="/cash">
            <span className="rl-glance__head">
              <span className="rl-glance__chip" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
              <span className="rl-glance__kicker">Cash in hand</span>
              <ChevronRight className="rl-icon rl-icon--sm rl-glance__chev" strokeWidth={1.75} aria-hidden />
            </span>
            <span className="rl-glance__big">{rupees(sum("balance_paise"))}</span>
            <span className="rl-glance__note">+{rupees(sum("in_paise"))} in, −{rupees(sum("out_paise"))} out today</span>
          </Link>
        )}
        <div className="rl-glance__pair">
          <Link className="rl-glance__cell rl-pressable" href="/collection">
            <span className="rl-glance__label"><span className="rl-glance__chip" aria-hidden="true"><Icon as={IndianRupee} size="sm" /></span>Collection today</span>
            <span className="rl-glance__value">{col.data ? rupees(col.data.total_paise) : "–"}</span>
            <span className="rl-glance__note">{col.data ? plural(col.data.count, "payment") : " "}</span>
          </Link>
          <Link className="rl-glance__cell rl-pressable" href="/expenses">
            <span className="rl-glance__label"><span className="rl-glance__chip" aria-hidden="true"><Icon as={Receipt} size="sm" /></span>Expenses today</span>
            <span className="rl-glance__value">{spent ? rupees(spent.total_paise) : "–"}</span>
            <span className="rl-glance__note">{spent ? (spent.count ? plural(spent.count, "expense") : "Nothing spent yet") : " "}</span>
          </Link>
        </div>
      </div>
      <div className="rl-glance__people rl-glance__people--four">
        {people.map((p) => (
          <Link className="rl-glance__cell rl-pressable" href={p.href} key={p.label}>
            <span className="rl-glance__label"><Icon as={p.icon} size="sm" />{p.label}</span>
            <span className={`rl-glance__value${p.tone && p.n ? ` rl-glance__value--${p.tone}` : ""}`}>{p.n?.toLocaleString("en-IN") ?? "–"}</span>
            <span className="rl-glance__note">{p.note}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

const DESK_ACTIONS = [
  { href: "/members/new", icon: UserPlus, label: "Add Member" },
  { href: "/payments/new", icon: Wallet, label: "Collect Payment" },
  { href: "/subscriptions/new", icon: Ticket, label: "New Subscription" },
];

export function ReceptionHome() {
  const { branch } = useSession();
  const today = isoDate(new Date());
  const counts = useGet<CheckinSummary>("/api/checkins/summary/", { date: today, branch });
  const [checking, setChecking] = useState(false);
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <Section label="Quick actions">
          <div className="rl-quick">
            <button className="rl-tile rl-tile--accent rl-pressable" type="button" onClick={() => setChecking(true)} aria-haspopup="dialog">
              <Icon as={ScanLine} /><span className="rl-tile__text">Check In Member<span className="rl-tile__hint">Search, then one tap</span></span><Icon as={ChevronRight} size="sm" />
            </button>
            {DESK_ACTIONS.map((a) => (
              <Link className="rl-tile rl-tile--stack rl-tile--desk rl-pressable" href={a.href} key={a.href}>
                <span className="rl-tile__plate" aria-hidden="true"><Icon as={a.icon} size="sm" /></span>
                <span className="rl-tile__label">{a.label}</span>
              </Link>
            ))}
          </div>
        </Section>
        <Section label="Today’s overview">
          <DeskGlance />
        </Section>
        <Section title="Check-ins today" aside={<p className="rl-section__aside">By session</p>}>
          {counts.data ? <SessionsTable sessions={counts.data.sessions} /> : <SkeletonRows n={3} />}
        </Section>
        <Section title="My tasks" aside={<Link className="rl-link" href="/tasks"><span>View all</span></Link>}><MyTasks /></Section>
      </main>
      <CheckInSheet open={checking} onClose={() => setChecking(false)} />
    </div>
  );
}

/** A trainer's own members at a glance, counted as on the admin's Home (active takes in those ending soon or owing):
 *  active, in today, and expired. */
function TrainerGlance({ mine }: { mine?: TrainerToday }) {
  const s = mine?.statuses;
  const n = (v?: number) => v?.toLocaleString("en-IN") ?? "–";
  const total = s && Object.values(s).reduce((t, v) => t + v, 0);
  const cells: { label: string; icon: LucideIcon; value?: number; note: string; href: string; tone?: "danger" }[] = [
    { label: "Active", icon: Users, value: s && s.active + s.expiring + s.due, note: s ? `${s.frozen} frozen` : " ", href: "/members?status=active" },
    { label: "In today", icon: CalendarCheck, value: mine?.in_today.length, note: total !== undefined ? `Of your ${plural(total, "member")}` : " ", href: "/attendance" },
    { label: "Expired", icon: CalendarX, value: s?.expired, note: "Not renewed yet", href: "/members?status=expired", tone: "danger" },
  ];
  return (
    <div className="rl-glance__people">
      {cells.map((c) => (
        <Link className="rl-glance__cell rl-pressable" href={c.href} key={c.label}>
          <span className="rl-glance__label"><Icon as={c.icon} size="sm" />{c.label}</span>
          <span className={`rl-glance__value${c.tone && c.value ? ` rl-glance__value--${c.tone}` : ""}`}>{n(c.value)}</span>
          <span className="rl-glance__note">{c.note}</span>
        </Link>
      ))}
    </div>
  );
}

/** The trainer's own check-in: the wall QR until they've checked in, then when and where they did. */
function TrainerCheckIn({ mine }: { mine: TrainerToday }) {
  if (mine.checked_in) {
    return (
      <div className="rl-card rl-card--pad">
        <p className="rl-statusline"><Icon as={CircleCheck} size="sm" />You checked in at {mine.checked_in.time}, {mine.checked_in.branch_name}.</p>
      </div>
    );
  }
  return (
    <Link className="rl-tile rl-tile--accent rl-pressable" href="/checkin">
      <Icon as={QrCode} /><span className="rl-tile__text">Check In<span className="rl-tile__hint">Scan the wall QR at the entrance</span></span><Icon as={ChevronRight} size="sm" />
    </Link>
  );
}

/** Their members' personal training, fewest sessions left first. A badge only when it says something: today's
 *  session done, or the plan ending or over. Tapping one opens the member, where Mark Session is. */
function PTClients({ rows }: { rows: TrainerToday["pt"] }) {
  const { role } = useSession();
  const today = gymToday(role.timezone);
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {rows.map((c) => {
        const { left, status } = ptState(c.pt, today);
        return (
          <li key={c.id}><Link className="rl-mrow" href={`/members/${c.id}`}>
            <Photo name={c.name} />
            <span className="rl-row__title rl-mrow__name">{c.name}</span>
            <span className="rl-row__meta rl-mrow__meta">{plural(left, "session")} left • Ends {day(c.pt.ends)}</span>
            {c.marked_today
              ? <span className="rl-pill rl-pill--soft" style={{ gridArea: "status", justifySelf: "end" }}><Icon as={Check} size="xs" />Done today</span>
              : status !== "active" && <Status status={status} />}
          </Link></li>
        );
      })}
    </ul>
  );
}

/** Their members who checked in today, latest first. */
function InToday({ rows }: { rows: TrainerToday["in_today"] }) {
  if (!rows.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>None of your members has checked in yet today.</p></div>;
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {rows.slice(0, 6).map((m) => (
        <li key={m.id}><Link className="rl-mrow" href={`/members/${m.id}`}>
          <Photo name={m.name} />
          <span className="rl-row__title rl-mrow__name">{m.name}</span>
          <span className="rl-row__meta rl-mrow__meta">{m.code} • {m.branch_name}</span>
          <span className="rl-mrow__time">{m.time}</span>
        </Link></li>
      ))}
    </ul>
  );
}

export function TrainerHome() {
  const { branch } = useSession();
  const q = useMembersTodayRetrieve(branch ? { branch } : undefined);
  const mine = q.data?.data;
  const counts = useGet<CheckinSummary>("/api/checkins/summary/", { date: isoDate(new Date()), branch });
  const needy = useMembersList({ status: "attention", limit: 5, ...(branch ? { branch } : {}) });
  const attention = (needy.data?.data.results ?? []) as unknown as TrainerMember[];
  const attentionCount = needy.data?.data.count ?? 0;
  const marked = mine?.pt.filter((c) => c.marked_today).length ?? 0;
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <Section label="Check in">
          {mine ? <TrainerCheckIn mine={mine} /> : <SkeletonRows n={1} />}
        </Section>
        <Section label="Today’s overview">
          <TrainerGlance mine={mine} />
        </Section>
        <div className="rl-app__cols">
          <div className="rl-app__col">
            {(mine?.pt.length ?? 0) > 0 && (
              <Section title="Personal training" aside={<p className="rl-section__aside">{marked} of {mine!.pt.length} done today</p>}>
                <PTClients rows={mine!.pt} />
              </Section>
            )}
            <Section title="Your members in today">
              {mine ? <InToday rows={mine.in_today} /> : <SkeletonRows n={2} />}
            </Section>
          </div>
          <div className="rl-app__col">
            <Section title="Follow up" aside={attentionCount > attention.length ? <Link className="rl-link" href="/members?status=attention"><span>See all {attentionCount}</span></Link> : undefined}>
              {needy.isLoading ? <SkeletonRows n={3} /> : attention.length ? (
                <ul className="rl-card rl-mlist rl-mlist--compact">
                  {attention.map((m) => (
                    <li key={m.id}><Link className="rl-mrow" href={`/members/${m.id}`}>
                      <Photo name={m.name} />
                      <span className="rl-row__title rl-mrow__name">{m.name}</span>
                      <span className="rl-row__meta rl-mrow__meta">{m.plan_ends ? `${m.plan_ends < isoDate(new Date()) ? "Ended" : "Ends"} ${day(m.plan_ends)}` : "No plan yet"}{m.payment_due && m.status !== "due" ? " • Payment due" : ""}</span>
                      <Status status={m.status} />
                    </Link></li>
                  ))}
                </ul>
              ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>All your members are active and paid up.</p></div>}
            </Section>
            <Section title="My tasks" aside={<Link className="rl-link" href="/tasks"><span>View all</span></Link>}><MyTasks /></Section>
          </div>
        </div>
        <Section title="Check-ins today" aside={<p className="rl-section__aside">By session</p>}>
          {counts.data ? <SessionsTable sessions={counts.data.sessions} /> : <SkeletonRows n={3} />}
        </Section>
      </main>
    </div>
  );
}

function streak(dates: string[]) {
  const set = new Set(dates);
  let n = 0;
  const d = new Date();
  if (!set.has(isoDate(d))) d.setDate(d.getDate() - 1);
  while (set.has(isoDate(d))) { n++; d.setDate(d.getDate() - 1); }
  return n;
}

export function MemberHome() {
  const meQ = useMembersList();
  const me = (meQ.data?.data.results?.[0] ?? null) as unknown as MemberSelf | null;
  const visits = useCheckinsList(me ? { member: me.id, limit: 60 } : undefined, { query: { enabled: !!me } });
  const v = visits.data?.data.results ?? [];
  const today = isoDate(new Date());
  const inToday = v.find((c) => c.local_date === today);
  const st = streak(v.map((c) => c.local_date));
  const plan = me?.plan;
  const days = plan ? planDays(plan.starts, plan.ends, today) : null;
  const passCls = me?.status === "expired" ? " rl-pass--expired" : me?.status === "expiring" ? " rl-pass--renew" : "";
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        {!me ? <SkeletonRows n={2} /> : (
          <>
            <Section label="Membership">
              <div className={`rl-pass${passCls}`}>
                <span className="rl-pass__top"><Status status={me.status} /><span className="rl-pass__plan">{plan?.name ?? "No plan yet"}</span></span>
                {plan && (
                  <>
                    <p className="rl-figure">{me.status === "expired" || !days ? 0 : days.left} <small>{me.status === "frozen" ? "days left, paused" : "days remaining"}</small></p>
                    {days && <Bar used={days.used} total={days.total} label={`${days.used} of ${days.total} days used`} />}
                    <span className="rl-pass__dates"><span>{day(plan.starts)}</span><span>{me.status === "expired" ? "Expired" : "Expires"} {day(plan.ends)}</span></span>
                  </>
                )}
                {me.pt && (
                  <div className="rl-sub">
                    <span><strong>Personal training:</strong> {sessionsUsed(me.pt)}{me.pt.trainer_name ? ` with ${me.pt.trainer_name}` : ""}</span>
                    <Bar used={me.pt.sessions_used} total={me.pt.sessions} label={sessionsUsed(me.pt)} />
                  </div>
                )}
                <PassActions>
                  <Link className="rl-button rl-button--soft rl-button--sm" href="/membership"><Icon as={Ticket} size="sm" />My Plans</Link>
                  <Link className="rl-button rl-button--soft rl-button--sm" href="/membership/payments"><Icon as={ReceiptText} size="sm" />My Payments</Link>
                </PassActions>
              </div>
              {me.balance_paise > 0 && <p className="rl-field__hint" style={{ marginTop: "var(--space-2)" }}>{rupees(me.balance_paise)} is due. Pay at the front desk.</p>}
            </Section>
            <Section label="Check in">
              {me.status === "expired" || me.status === "none" ? (
                <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Your plan has ended. Renew it at the front desk to check in again.</p></div>
              ) : me.status === "frozen" ? (
                <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Your plan is paused{plan?.frozen_until ? ` until ${day(plan.frozen_until)}` : ""}. Ask the front desk to unfreeze it if you&apos;re back early.</p></div>
              ) : inToday ? (
                <div className="rl-card rl-card--pad"><p className="rl-statusline" style={{ margin: 0 }}><Icon as={CircleCheck} size="sm" />You checked in today at {inToday.time}, {inToday.branch_name}.</p></div>
              ) : (
                // The same tile as the staff's own check-in on Trainer Home: one tap opens the wall QR scanner.
                <Link className="rl-tile rl-tile--accent rl-pressable" href="/checkin">
                  <Icon as={QrCode} /><span className="rl-tile__text">Check In<span className="rl-tile__hint">Scan the wall QR at the entrance</span></span><Icon as={ChevronRight} size="sm" />
                </Link>
              )}
            </Section>
            <MyPlansRows />
            <Section title="Attendance streak">
              <div className="rl-card rl-card--pad rl-streak">
                <p className="rl-figure" style={{ margin: 0 }}>{st} 🔥 <small>{st === 1 ? "day" : "days"} in a row</small></p>
                <p className="rl-row__meta" style={{ margin: 0 }}>
                  {st ? (inToday ? `You've checked in ${st} days in a row. Come back tomorrow to make it ${st + 1}.` : `You've checked in ${st} days in a row. Check in today to make it ${st + 1}.`) : "Check in today to start a streak."}
                </p>
              </div>
            </Section>
            <Section title="Recent visits" aside={<Link className="rl-link" href="/visits"><span>View all</span></Link>}>
              {v.length ? (
                <ul className="rl-card rl-mlist rl-mlist--compact">
                  {v.slice(0, 5).map((c) => (
                    <li key={c.id}><div className="rl-mrow">
                      <span className="rl-chipicon" aria-hidden="true"><Icon as={CalendarCheck} size="sm" /></span>
                      <span className="rl-row__title rl-mrow__name">{c.local_date === today ? "Today" : day(c.local_date)}</span>
                      <span className="rl-row__meta rl-mrow__meta">{c.branch_name}{c.session ? ` • ${c.session}` : ""}</span>
                      <span className="rl-mrow__time">{c.time}</span>
                    </div></li>
                  ))}
                </ul>
              ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Your visits will show here.</p></div>}
            </Section>
          </>
        )}
      </main>
    </div>
  );
}
