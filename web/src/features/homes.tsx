"use client";
import {
  AlertTriangle, CalendarCheck, CalendarX, ChevronRight, ClipboardCheck, HandCoins, IndianRupee, ListChecks, QrCode, ScanLine, Ticket,
  UserPlus, Users, Wallet,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useRef } from "react";

import { useBranchesList } from "@/api/gen/branches/branches";
import { useCheckinsList } from "@/api/gen/checkins/checkins";
import { useMembersList } from "@/api/gen/members/members";
import { useStaffList } from "@/api/gen/staff/staff";
import { useTasksList } from "@/api/gen/tasks/tasks";
import { Greeting, HomeBar } from "@/components/shell";
import { Icon, Photo, Section, SkeletonRows, Stat, Status, TaskStatus } from "@/components/ui";
import { day, daysLeft, isoDate, plural, rupees, span } from "@/lib/format";
import { useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { CheckinSummary, MemberSelf, Page, SessionCounts, Summary, TaskCounts, TrainerMember } from "@/lib/types";

import { CheckInSearch } from "./checkin";

function Attention({ rows }: { rows: { count: number; title: string; meta: string; href: string }[] }) {
  const shown = rows.filter((r) => r.count > 0);
  if (!shown.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Nothing needs you right now.</p></div>;
  return (
    <ul className="rl-attn">
      {shown.map((r) => (
        <li key={r.title}><Link className="rl-attn__row" href={r.href}>
          <span className="rl-attn__count">{r.count}</span>
          <span className="rl-attn__text"><span className="rl-row__title">{r.title}</span><span className="rl-row__meta">{r.meta}</span></span>
          <ChevronRight className="rl-icon rl-icon--sm rl-attn__chev" strokeWidth={1.75} aria-hidden />
        </Link></li>
      ))}
    </ul>
  );
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

export function AdminHome() {
  const { branch } = useSession();
  const s = useGet<Summary>("/api/reports/summary/", { branch });
  const tasks = useGet<TaskCounts>("/api/tasks/counts/");
  const staff = useStaffCounts();
  const sum = s.data;
  const late = tasks.data?.overdue ?? 0;
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <Section label="Today’s overview">
          <div className="rl-scroller rl-scroller--five">
            {!sum ? Array.from({ length: 4 }, (_, i) => <div className="rl-stat" key={i}><span className="rl-skel" style={{ height: 28, width: "70%" }} /><span className="rl-skel" style={{ height: 14, width: "50%", marginTop: 8 }} /></div>) : (
              <>
                <Stat icon={IndianRupee} value={rupees(sum.revenue.today_paise)} label="Today’s revenue" note={`${rupees(sum.revenue.month_paise)} this month`} href="/reports" />
                <Stat icon={Users} value={(sum.members.active + sum.members.expiring + sum.members.due).toLocaleString("en-IN")} label="Active members" note={`${sum.members.frozen} frozen`} href="/members?status=active" />
                <Stat icon={CalendarCheck} value={sum.checkins.total} label="Check-ins today" href="/attendance" />
                <Stat icon={CalendarX} value={sum.members.expired} label="Expired" note="Not renewed yet" href="/members?status=expired" />
                <Stat icon={HandCoins} value={rupees(sum.dues.total_paise)} label="Outstanding dues" note={`From ${plural(sum.dues.members, "member")}`} href="/members?status=due" />
              </>
            )}
          </div>
        </Section>
        <div className="rl-app__cols">
          <div className="rl-app__col">
            <Section title="Quick actions">
              <div className="rl-tiles">
                <Link className="rl-tile rl-tile--primary rl-pressable" href="/members/new"><Icon as={UserPlus} /><span>Add Member</span></Link>
                <Link className="rl-tile rl-tile--primary rl-pressable" href="/payments/new"><Icon as={Wallet} /><span>Collect Payment</span></Link>
                <Link className="rl-tile rl-pressable" href="/subscriptions/new"><Icon as={Ticket} /><span>New Subscription</span></Link>
                <Link className="rl-tile rl-pressable" href="/attendance?checkin=1"><Icon as={ClipboardCheck} /><span>Mark Attendance</span></Link>
              </div>
            </Section>
            <Section title="Needs attention">
              {sum ? <Attention rows={[
                { count: sum.members.expiring, title: "Memberships expiring soon", meta: "In the next 7 days", href: "/members?status=expiring" },
                { count: sum.dues.members, title: "Pending payments", meta: `${rupees(sum.dues.total_paise)} due`, href: "/members?status=due" },
                { count: late, title: "Overdue tasks", meta: "Past their due time", href: "/tasks?filter=overdue" },
              ]} /> : <SkeletonRows n={2} />}
            </Section>
          </div>
          <div className="rl-app__col">
            <Section title="Check-ins today" aside={<p className="rl-section__aside">By session</p>}>
              {sum ? <SessionsTable sessions={sum.checkins.sessions} staff={staff} /> : <SkeletonRows n={3} />}
            </Section>
          </div>
        </div>
      </main>
    </div>
  );
}

export function ReceptionHome() {
  const { branch } = useSession();
  const today = isoDate(new Date());
  const counts = useGet<CheckinSummary>("/api/checkins/summary/", { date: today, branch });
  const expiring = useGet<Page<unknown>>("/api/members/", { status: "expiring", limit: 1, branch });
  const due = useGet<Page<unknown>>("/api/members/", { status: "due", limit: 1, branch });
  const searchRef = useRef<HTMLDivElement>(null);
  const focusSearch = () => searchRef.current?.querySelector("input")?.focus();
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <div ref={searchRef}><CheckInSearch /></div>
        <Section label="Quick actions">
          <div className="rl-quick">
            <button className="rl-tile rl-tile--accent rl-pressable" type="button" onClick={focusSearch}>
              <Icon as={ScanLine} /><span className="rl-tile__text">Check In Member<span className="rl-tile__hint">Search, then one tap</span></span><Icon as={ChevronRight} size="sm" />
            </button>
            <Link className="rl-tile rl-tile--stack rl-pressable" href="/members/new"><Icon as={UserPlus} /><span>Add Member</span></Link>
            <Link className="rl-tile rl-tile--stack rl-pressable" href="/payments/new"><Icon as={Wallet} /><span>Collect Payment</span></Link>
            <Link className="rl-tile rl-tile--stack rl-pressable" href="/subscriptions/new"><Icon as={Ticket} /><span>New Subscription</span></Link>
          </div>
        </Section>
        <Section label="Today’s overview">
          <div className="rl-scroller">
            <Stat icon={CalendarCheck} value={counts.data?.totals.member ?? "–"} label="Check-ins today" href="/attendance" />
            <Stat icon={AlertTriangle} value={expiring.data?.count ?? "–"} label="Expiring this week" note={<Status status="expiring" />} href="/members?status=expiring" />
            <Stat icon={HandCoins} value={due.data?.count ?? "–"} label="Payment due" href="/members?status=due" />
          </div>
        </Section>
        <Section title="Check-ins today" aside={<p className="rl-section__aside">By session</p>}>
          {counts.data ? <SessionsTable sessions={counts.data.sessions} /> : <SkeletonRows n={3} />}
        </Section>
        <Section title="My tasks" aside={<Link className="rl-link" href="/tasks"><span>View all</span></Link>}><MyTasks /></Section>
      </main>
    </div>
  );
}

export function TrainerHome() {
  const mine = useMembersList({ limit: 1 });
  const needy = useMembersList({ status: "attention", limit: 6 });
  const attention = (needy.data?.data.results ?? []) as unknown as TrainerMember[];
  const attentionCount = needy.data?.data.count ?? 0;
  return (
    <div className="rl-app rl-root">
      <HomeBar />
      <main className="rl-app__main">
        <Greeting />
        <Section label="Overview">
          <div className="rl-kpis rl-kpis--pair">
            <Stat icon={Users} value={mine.isLoading ? "–" : mine.data?.data.count ?? 0} label="My members" href="/members" />
            <Stat icon={AlertTriangle} value={needy.isLoading ? "–" : attentionCount} label="Need attention" href="/members?status=attention" />
          </div>
        </Section>
        <Section title="My tasks" aside={<Link className="rl-link" href="/tasks"><span>View all</span></Link>}><MyTasks /></Section>
        <Section title="Members to follow up">
          {needy.isLoading ? <SkeletonRows n={3} /> : attention.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {attention.map((m) => (
                <li key={m.id}><Link className="rl-mrow" href={`/members/${m.id}`}>
                  <Photo name={m.name} />
                  <span className="rl-row__title rl-mrow__name">{m.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{m.code}{m.plan_ends ? ` • Plan ends ${day(m.plan_ends)}` : ""}</span>
                  <Status status={m.status} />
                </Link></li>
              ))}
            </ul>
          ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>All your members are active and paid up.</p></div>}
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
  const total = plan ? Math.max(1, (new Date(plan.ends).getTime() - new Date(plan.starts).getTime()) / 864e5 + 1) : 1;
  const left = plan ? Math.max(0, daysLeft(plan.ends) + 1) : 0;
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
                    <p className="rl-figure">{me.status === "expired" ? 0 : left} <small>{me.status === "frozen" ? "days left, paused" : "days remaining"}</small></p>
                    <span className="rl-bar" role="img" aria-label={`${Math.round(total - left)} of ${Math.round(total)} days used`}><span className="rl-bar__fill" style={{ ["--v" as string]: Math.min(1, (total - left) / total) }} /></span>
                    <span className="rl-pass__dates"><span>{day(plan.starts)}</span><span>{me.status === "expired" ? "Expired" : "Expires"} {day(plan.ends)}</span></span>
                  </>
                )}
              </div>
              {me.balance_paise > 0 && <p className="rl-field__hint" style={{ marginTop: "var(--space-2)" }}>{rupees(me.balance_paise)} is due. Pay at the front desk.</p>}
            </Section>
            <Section label="Check in">
              {me.status === "expired" || me.status === "none" ? (
                <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Your plan has ended. Renew it at the front desk to check in again.</p></div>
              ) : me.status === "frozen" ? (
                <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Your plan is paused{plan?.frozen_until ? ` until ${day(plan.frozen_until)}` : ""}. Ask the front desk to unfreeze it if you&apos;re back early.</p></div>
              ) : inToday ? (
                <div className="rl-card rl-card--pad"><p className="rl-statusline" style={{ margin: 0 }}>You checked in today at {inToday.time}, {inToday.branch_name}.</p></div>
              ) : (
                <Link className="rl-button rl-button--accent rl-button--block" href="/checkin"><Icon as={QrCode} />Check In</Link>
              )}
            </Section>
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
