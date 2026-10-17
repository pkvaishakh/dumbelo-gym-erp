"use client";
/* The cards on Admin → Reports. Every card answers to the screen's one period and one branch (see Reports.md). */
import { format, parseISO } from "date-fns";
import { ClipboardList, Minus, TrendingDown, TrendingUp } from "lucide-react";
import Link from "next/link";

import { Chart, type ChartPoint } from "@/components/chart";
import { Empty, Icon, Photo, Section, TaskStatus } from "@/components/ui";
import { clock, day, plural, rangeLabel, rupees, rupeesShort, trend } from "@/lib/format";
import type { PeriodReport, Summary } from "@/lib/types";

type Day = PeriodReport["series"][number];

/** "+9% vs previous 7 days", with an arrow. Text in ink: the arrow carries the direction, not a colour. */
export function Trend({ now, before, days }: { now: number; before: number; days: number }) {
  const t = trend(now, before, days);
  return <><Icon as={t.dir === "up" ? TrendingUp : t.dir === "down" ? TrendingDown : Minus} size="xs" /><span>{t.text}</span></>;
}

/** The chart's points: one a day up to a month, then one a week, since daily money over months is mostly noise. */
function points(r: PeriodReport, value: (d: Day) => number, text: (n: number) => string, today: string): ChartPoint[] {
  if (r.days > 31) {
    // Weeks end on the last day, so a short week falls at the start rather than looking like a drop at the end.
    const weeks: ChartPoint[] = [];
    for (let end = r.series.length; end > 0; end -= 7) {
      const chunk = r.series.slice(Math.max(0, end - 7), end);
      const total = chunk.reduce((sum, d) => sum + value(d), 0);
      const start = parseISO(chunk[0]!.date);
      weeks.unshift({ tick: format(start, "d MMM"), label: `Week of ${format(start, "d MMM")}`, value: total, text: text(total) });
    }
    return weeks;
  }
  return r.series.map((d) => {
    const at = parseISO(d.date);
    const tick = r.days <= 7 ? (d.date === today ? "Today" : format(at, "EEE")) : format(at, "d MMM");
    return { tick, label: format(at, "EEE d MMM"), value: value(d), text: text(value(d)) };
  });
}

function SeriesChart({ r, label, value, text, axis, cap, today }: {
  r: PeriodReport; label: string; value: (d: Day) => number; text: (n: number) => string;
  axis: (n: number) => string; cap: (n: number) => string; today: string;
}) {
  return <Chart points={points(r, value, text, today)} label={label} axis={axis} cap={cap} latest={r.to === today} line={r.days > 14} />;
}

export function BarList({ rows }: { rows: { key: string; label: string; value: number; text: string }[] }) {
  const max = Math.max(1, ...rows.map((x) => x.value));
  return (
    <ul className="rl-barlist">
      {rows.map((x) => (
        <li key={x.key}>
          <div className="rl-barlist__top"><span>{x.label}</span><span>{x.text}</span></div>
          <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: x.value / max }} /></span>
        </li>
      ))}
    </ul>
  );
}

const lastDays = (r: PeriodReport) => rangeLabel(r.from, r.to);

export function RevenueCard({ r, today }: { r: PeriodReport; today: string }) {
  return (
    <Section title="Revenue">
      <div className="rl-card rl-card--pad rl-report">
        <p className="rl-report__value">{rupees(r.totals.revenue_paise)}</p>
        <p className="rl-perf__label">Collected, {lastDays(r)}</p>
        <p className="rl-trend"><Trend now={r.totals.revenue_paise} before={r.previous.revenue_paise} days={r.days} /></p>
        <SeriesChart r={r} today={today} label={`Revenue, ${lastDays(r)}`} value={(d) => d.revenue_paise} text={rupees} axis={rupeesShort} cap={rupeesShort} />
        {r.revenue_by_plan.length > 0 && (
          <>
            <p className="rl-report__sub">By plan</p>
            <BarList rows={r.revenue_by_plan.map((p) => ({ key: p.name, label: p.name, value: p.paise, text: rupees(p.paise) }))} />
          </>
        )}
      </div>
    </Section>
  );
}

export function MoneyCard({ r }: { r: PeriodReport }) {
  const left = r.totals.revenue_paise - r.totals.expenses_paise;
  return (
    <Section title="Money in and out" aside={<Link className="rl-link" href="/expenses"><span>View expenses</span></Link>}>
      <div className="rl-card rl-card--pad rl-report">
        <dl className="rl-facts"><dt>Revenue</dt><dd>{rupees(r.totals.revenue_paise)}</dd><dt>Expenses</dt><dd>{rupees(r.totals.expenses_paise)}</dd></dl>
        {/* Not "profit": it leaves out anything not entered as an expense. */}
        <div className="rl-total"><span>Left over</span><span>{left < 0 ? "-" : ""}{rupees(Math.abs(left))}</span></div>
        {r.expenses_by_category.length > 0 && (
          <>
            <p className="rl-report__sub">Expenses by category</p>
            <BarList rows={r.expenses_by_category.map((c) => ({ key: c.category, label: c.label, value: c.paise, text: rupees(c.paise) }))} />
          </>
        )}
      </div>
    </Section>
  );
}

export function MembersCard({ r, s, today }: { r: PeriodReport; s?: Summary; today: string }) {
  const active = s ? s.members.active + s.members.expiring + s.members.due : null;
  return (
    <Section title="Members">
      <div className="rl-card rl-card--pad rl-report">
        <p className="rl-report__value">{r.totals.new_members.toLocaleString("en-IN")}</p>
        <p className="rl-perf__label">New members, {lastDays(r)}</p>
        <p className="rl-trend"><Trend now={r.totals.new_members} before={r.previous.new_members} days={r.days} /></p>
        <SeriesChart r={r} today={today} label={`New members, ${lastDays(r)}`} value={(d) => d.new_members} text={(n) => plural(n, "new member")} axis={String} cap={String} />
        <dl className="rl-facts">
          <dt>Renewed</dt><dd>{r.totals.renewals.toLocaleString("en-IN")}</dd>
          {active !== null && <><dt>Active on {day(r.to)}</dt><dd>{active.toLocaleString("en-IN")}</dd></>}
          {s && <><dt>Dues outstanding</dt><dd>{rupees(s.dues.total_paise)}</dd></>}
        </dl>
      </div>
    </Section>
  );
}

const WEEK = [1, 2, 3, 4, 5, 6, 0]; // Monday first
const WEEKDAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export function AttendanceCard({ r, today }: { r: PeriodReport; today: string }) {
  // Over two weeks or more, a typical week says more than one long row of days.
  const byWeekday = r.days >= 14 ? WEEK.map((wd) => {
    const days = r.series.filter((d) => parseISO(d.date).getDay() === wd);
    const avg = days.length ? Math.round(days.reduce((sum, d) => sum + d.checkins, 0) / days.length) : 0;
    return { key: String(wd), label: WEEKDAY[wd]!, value: avg, text: `${avg.toLocaleString("en-IN")} a day` };
  }) : [];
  const busiest = byWeekday.reduce<(typeof byWeekday)[number] | null>((b, x) => (!b || x.value > b.value ? x : b), null);
  return (
    <Section title="Attendance" aside={<Link className="rl-link" href="/attendance"><span>View attendance</span></Link>}>
      <div className="rl-card rl-card--pad rl-report">
        <p className="rl-report__value">{r.totals.checkins.toLocaleString("en-IN")}</p>
        <p className="rl-perf__label">Member check-ins, {lastDays(r)}</p>
        <p className="rl-trend"><Trend now={r.totals.checkins} before={r.previous.checkins} days={r.days} /></p>
        <SeriesChart r={r} today={today} label={`Check-ins, ${lastDays(r)}`} value={(d) => d.checkins} text={(n) => plural(n, "check-in")} axis={String} cap={String} />
        {busiest && busiest.value > 0 && (
          <>
            <p className="rl-report__sub">Average by day of the week</p>
            <BarList rows={byWeekday.map((x) => (x === busiest ? { ...x, label: `${x.label} · busiest` } : x))} />
          </>
        )}
      </div>
    </Section>
  );
}

const ROLE = { trainer: "Trainer", receptionist: "Receptionist" } as const;

export function TasksCard({ r }: { r: PeriodReport }) {
  const t = r.tasks;
  if (!t.total) {
    return (
      <Section title="Tasks">
        <Empty icon={ClipboardList} title="No tasks due in these days" text="Tasks you give trainers and receptionists show up here by their due date.">
          <Link className="rl-button rl-button--secondary" href="/tasks?new=1">New Task</Link>
        </Empty>
      </Section>
    );
  }
  const share = t.done / t.total;
  return (
    <Section title="Tasks" aside={<Link className="rl-link" href="/tasks?filter=all"><span>View tasks</span></Link>}>
      <div className="rl-card rl-card--pad rl-report">
        <p className="rl-report__value">{t.done} of {t.total} done</p>
        <p className="rl-perf__label">Tasks due {lastDays(r)}</p>
        <p className="rl-trend"><Trend now={r.totals.tasks_done} before={r.previous.tasks_done} days={r.days} /></p>
        <span className="rl-bar" role="img" aria-label={`${Math.round(share * 100)}% done`} style={{ height: 8, marginTop: "var(--space-4)", background: "var(--surface)" }}>
          <span className="rl-bar__fill" style={{ ["--v" as string]: share }} />
        </span>
        <dl className="rl-facts">
          <dt>To do</dt><dd>{t.todo}</dd>
          <dt>In progress</dt><dd>{t.doing}</dd>
          <dt>Done</dt><dd>{t.done}</dd>
          <dt>Overdue</dt><dd style={t.overdue ? { color: "var(--attention)" } : undefined}>{t.overdue}</dd>
        </dl>
        <p className="rl-report__sub">By person</p>
        <ul className="rl-barlist">
          {t.people.map((p) => (
            <li key={p.id}>
              <div className="rl-barlist__top"><span>{p.name}</span><span>{p.done} of {p.total} done</span></div>
              <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: p.done / p.total }} /></span>
              <p className="rl-row__meta" style={{ margin: "4px 0 0" }}>
                {ROLE[p.role]}{p.overdue > 0 && <> · <span style={{ color: "var(--attention)", fontWeight: 600 }}>{plural(p.overdue, "overdue task")}</span></>}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

/** The oldest overdue tasks in the period, each opening on the Tasks screen. */
export function LateTasks({ r }: { r: PeriodReport }) {
  const { late, overdue } = r.tasks;
  if (!late.length) return null;
  return (
    <Section title="Overdue tasks" aside={overdue > late.length ? <Link className="rl-link" href="/tasks?filter=overdue"><span>See all {overdue}</span></Link> : undefined}>
      <ul className="rl-card rl-mlist rl-mlist--compact">
        {late.map((t) => (
          <li key={t.id}><Link className="rl-mrow rl-tkrow" href={`/tasks?open=${t.id}`}>
            <Photo name={t.assignee_name} />
            <span className="rl-row__title rl-mrow__name">{t.title}</span>
            <span className="rl-row__meta rl-mrow__meta">{t.assignee_name} • Due {day(t.due_date)}{t.due_time ? `, ${clock(t.due_time)}` : ""}</span>
            <TaskStatus status="todo" overdue />
          </Link></li>
        ))}
      </ul>
    </Section>
  );
}
