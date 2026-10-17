"use client";
import { addDays, differenceInCalendarDays, parseISO, subMonths } from "date-fns";
import { BarChart3, CalendarCheck, ClipboardCheck, IndianRupee, UserPlus } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { BranchChip, PageBar } from "@/components/shell";
import { Empty, Field, Section, Seg, SkeletonRows, Stat } from "@/components/ui";
import { AttendanceCard, LateTasks, MembersCard, MoneyCard, RevenueCard, TasksCard, Trend } from "@/features/reports";
import { isoDate, rangeLabel, rupees } from "@/lib/format";
import { useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { PeriodReport, Summary } from "@/lib/types";

type Period = "7d" | "30d" | "3m" | "custom";
const PERIODS: { value: Period; label: string }[] = [
  { value: "7d", label: "7 days" }, { value: "30d", label: "30 days" }, { value: "3m", label: "3 months" }, { value: "custom", label: "Custom" },
];
const MAX_DAYS = 366; // the API's limit too

/** The first and last day a period covers, ending today unless the range is custom. */
function rangeOf(period: Period, today: string, from: string | null, to: string | null): [string, string] {
  const t = parseISO(today);
  if (period === "30d") return [isoDate(addDays(t, -29)), today];
  if (period === "3m") return [isoDate(addDays(subMonths(t, 3), 1)), today];
  if (period === "custom") return [from || isoDate(addDays(t, -6)), to || today];
  return [isoDate(addDays(t, -6)), today];
}

function rangeError(from: string, to: string) {
  if (from > to) return "Pick a start date on or before the end date";
  if (differenceInCalendarDays(parseISO(to), parseISO(from)) >= MAX_DAYS) return "Pick a range of a year or less";
  return undefined;
}

function ReportsPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { branch } = useSession();
  const today = isoDate(new Date());
  const period = (PERIODS.some((p) => p.value === params.get("period")) ? params.get("period") : "7d") as Period;
  const [from, to] = rangeOf(period, today, params.get("from"), params.get("to"));
  const error = rangeError(from, to);

  // Filters live in the URL, so Back and a shared link keep them.
  const go = (next: Record<string, string>) => router.replace(`/reports?${new URLSearchParams(next)}`, { scroll: false });
  const pick = (p: Period) => go(p === "custom" ? { period: p, from, to } : p === "7d" ? {} : { period: p });

  const r = useGet<PeriodReport>("/api/reports/period/", { from, to, branch }, !error);
  const s = useGet<Summary>("/api/reports/summary/", { date: to, branch }, !error).data;
  const rep = r.data;

  return (
    <div className="rl-app rl-root">
      <PageBar title="Reports" sub={rangeLabel(from, to)} action={<BranchChip />} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--period">
          <Seg label="Period" value={period} onChange={pick} options={PERIODS} onSurface />
        </div>
        {period === "custom" && (
          <div className="rl-pair" style={{ marginTop: "var(--space-4)" }}>
            <Field label="From" error={error}>{(id, desc) => (
              <input className="rl-field__input" id={id} type="date" max={today} value={from} aria-describedby={desc} aria-invalid={!!error}
                onChange={(e) => e.target.value && go({ period, from: e.target.value, to })} />
            )}</Field>
            <Field label="To">{(id) => (
              <input className="rl-field__input" id={id} type="date" max={today} value={to}
                onChange={(e) => e.target.value && go({ period, from, to: e.target.value })} />
            )}</Field>
          </div>
        )}

        {error ? null : r.error ? (
          <Empty icon={BarChart3} title="This report didn't load" text={r.error.message}>
            <button className="rl-button rl-button--secondary" type="button" onClick={() => r.refetch()}>Try Again</button>
          </Empty>
        ) : !rep ? <SkeletonRows n={6} /> : (
          <>
            <Section label="Summary">
              <div className="rl-kpis">
                <Stat icon={IndianRupee} accent value={rupees(rep.totals.revenue_paise)} label="Revenue" note={<Trend now={rep.totals.revenue_paise} before={rep.previous.revenue_paise} days={rep.days} />} />
                <Stat icon={UserPlus} value={rep.totals.new_members.toLocaleString("en-IN")} label="New members" note={<Trend now={rep.totals.new_members} before={rep.previous.new_members} days={rep.days} />} />
                <Stat icon={CalendarCheck} value={rep.totals.checkins.toLocaleString("en-IN")} label="Check-ins" note={<Trend now={rep.totals.checkins} before={rep.previous.checkins} days={rep.days} />} />
                <Stat icon={ClipboardCheck} value={`${rep.tasks.done} of ${rep.tasks.total}`} label="Tasks done" note={<Trend now={rep.totals.tasks_done} before={rep.previous.tasks_done} days={rep.days} />} />
              </div>
            </Section>
            <div className="rl-app__cols">
              <div className="rl-app__col">
                <RevenueCard r={rep} today={today} />
                <MoneyCard r={rep} />
                <TasksCard r={rep} />
              </div>
              <div className="rl-app__col">
                <MembersCard r={rep} s={s} today={today} />
                <AttendanceCard r={rep} today={today} />
                <LateTasks r={rep} />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><ReportsPage /></Suspense>; }
