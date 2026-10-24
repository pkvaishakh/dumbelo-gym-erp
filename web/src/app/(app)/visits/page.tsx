"use client";
import { CalendarCheck } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { useCheckinsListInfinite } from "@/api/gen/checkins/checkins";
import type { CheckIn, CheckinsListParams } from "@/api/gen/model";
import { useMembersRetrieve } from "@/api/gen/members/members";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Field, Icon, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { day, isoDate, plural, rangeLabel } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";
import { historyPeriod, HISTORY_PERIODS, type Period, rangeOf } from "@/lib/periods";
import { useSession } from "@/lib/session";

/** A member's own visits; a staff member's own check-ins (More, My Attendance); with `?member=`, staff see that
 *  member's, from Visits in their profile's Member actions. */
function VisitsPage() {
  const member = Number(useSearchParams().get("member")) || 0;
  const { role } = useSession();
  if (member) return <MemberVisits id={member} />;
  return role.role === "member" ? <MyVisits /> : <MyAttendance />;
}

function MyVisits() {
  const q = useCheckinsListInfinite(undefined, { query: paged });
  const { rows } = pages(q);
  const today = isoDate(new Date());
  // One check-in a day, latest first: the first page (50) always holds the whole of this month.
  const month = rows.filter((c) => c.local_date.slice(0, 7) === today.slice(0, 7)).length;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Visits" sub={`${plural(month, "visit")} this month`} />
      <main className="rl-app__main">
        <section className="rl-section">
          {q.isLoading ? <SkeletonRows /> : rows.length ? <><VisitRows rows={rows} today={today} /><LoadMore q={q} /></>
            : <Empty icon={CalendarCheck} title="No visits yet" text="Each time you check in, it shows up here." />}
        </section>
      </main>
    </div>
  );
}

/** One member's visits for the desk or their trainer. */
function MemberVisits({ id }: { id: number }) {
  const who = useMembersRetrieve(id).data?.data;
  return <VisitHistory filter={{ member: id }} keep={{ member: String(id) }} title="Visits" sub={who?.name ?? ""} back={`/members/${id}`}
    noun="visit" empty={`Each time ${who?.name ?? "they"} checks in, it shows up here.`} />;
}

/** A staff member's own check-ins, at any branch: the days they came in, which their pay by days present counts. */
function MyAttendance() {
  return <VisitHistory filter={{ mine: true }} keep={{}} title="My Attendance" sub="Your check-ins" back="/more"
    noun="check-in" empty="Each time you check in, by the wall QR, the desk or the turnstile, it shows up here." />;
}

/** One person's check-ins: every one at first, or the days picked. The period lives in the address, so Back and a
 *  shared link keep it; `keep` is the rest of the address. */
function VisitHistory({ filter, keep, title, sub, back, noun, empty }: {
  filter: CheckinsListParams; keep: Record<string, string>; title: string; sub: string; back: string; noun: string; empty: string;
}) {
  const params = useSearchParams();
  const router = useRouter();
  const today = isoDate(new Date());
  const period = historyPeriod(params.get("period"));
  const [from, to] = rangeOf(period, today, params.get("from"), params.get("to"));
  const backwards = from > to;
  const q = useCheckinsListInfinite({ ...filter, ...(period !== "all" ? { from, to } : {}) }, { query: { ...paged, enabled: !backwards } });
  const { rows, count } = pages(q);

  const go = (next: Period, days: { from?: string; to?: string } = {}) => {
    const p = new URLSearchParams(keep);
    if (next !== "all") p.set("period", next);
    if (next === "custom") { p.set("from", days.from ?? (from || today)); p.set("to", days.to ?? (to || today)); }
    router.replace(`/visits?${p}`, { scroll: false });
  };

  return (
    <div className="rl-app rl-root">
      <PageBar title={title} sub={sub} back={back} />
      <main className="rl-app__main">
        <Chips name="visits-period" label="Period" value={period} onChange={(v) => go(v)} options={HISTORY_PERIODS} />
        {period === "custom" && (
          <div className="rl-pair" style={{ marginTop: "var(--space-4)" }}>
            <Field label="From" error={backwards ? "Pick a start date on or before the end date" : undefined}>{(fid, desc) => (
              <input className="rl-field__input" id={fid} type="date" max={today} value={from} aria-describedby={desc} aria-invalid={backwards}
                onChange={(e) => e.target.value && go("custom", { from: e.target.value })} />
            )}</Field>
            <Field label="To">{(fid) => (
              <input className="rl-field__input" id={fid} type="date" max={today} value={to} onChange={(e) => e.target.value && go("custom", { to: e.target.value })} />
            )}</Field>
          </div>
        )}
        {!backwards && (
          <Section title={period === "all" ? `All ${noun}s` : from === to ? day(from) : rangeLabel(from, to)}>
            <div className="rl-listmeta">
              <p role="status">{q.isLoading ? "Loading…" : `Showing ${plural(rows.length, noun)}${rows.length < count ? ` of ${count}` : ""}`}</p>
              <p>Newest first</p>
            </div>
            {q.isLoading ? <SkeletonRows /> : rows.length ? <><VisitRows rows={rows} today={today} /><LoadMore q={q} /></>
              : period === "all" ? <Empty icon={CalendarCheck} title={`No ${noun}s yet`} text={empty} />
              : <Empty icon={CalendarCheck} title={from === to ? `No ${noun} this day` : `No ${noun}s in these dates`} text={`Try All time to see every ${noun}.`} />}
          </Section>
        )}
      </main>
    </div>
  );
}

/** Check-ins as a list: the day, the branch and session, and the time in. */
function VisitRows({ rows, today }: { rows: CheckIn[]; today: string }) {
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {rows.map((c) => (
        <li key={c.id}><div className="rl-mrow">
          <span className="rl-chipicon" aria-hidden="true"><Icon as={CalendarCheck} size="sm" /></span>
          <span className="rl-row__title rl-mrow__name">{c.local_date === today ? "Today" : day(c.local_date)}</span>
          <span className="rl-row__meta rl-mrow__meta">{c.branch_name}{c.session ? ` • ${c.session}` : ""}</span>
          <span className="rl-mrow__time">{c.time}</span>
        </div></li>
      ))}
    </ul>
  );
}

export default function Page() {
  return <Suspense><VisitsPage /></Suspense>;
}
