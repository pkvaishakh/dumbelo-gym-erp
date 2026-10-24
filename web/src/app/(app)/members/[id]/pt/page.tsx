"use client";
/* A member's personal training in full: the plan, how they're using it, what they've worked, and every session given.
 * Opened from the eye on the profile's Personal training card. No amounts: trainers see this too. */
import { CalendarCheck, CalendarDays, CircleCheck, Dumbbell, Gauge, Snowflake, UserRound } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useMembersRetrieve } from "@/api/gen/members/members";
import type { PTSession } from "@/api/gen/model";
import { usePtSessionsListInfinite } from "@/api/gen/pt-sessions/pt-sessions";
import { PageBar } from "@/components/shell";
import { Bar, Details, Empty, Icon, LoadMore, Section, SkeletonRows, Status } from "@/components/ui";
import { SessionSheet, sessionMeta } from "@/features/pt";
import { day, gymToday, plural } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";
import { partCounts, ptPace, ptState, sessionsUsed } from "@/lib/pt";
import { useSession } from "@/lib/session";

export default function PTDetails() {
  const { id } = useParams<{ id: string }>();
  const mid = Number(id);
  const { role } = useSession();
  const today = gymToday(role.timezone);
  const m = useMembersRetrieve(mid).data?.data;
  const pt = m?.pt ?? null;
  // Every session, newest first; one removed by mistake stays on record, crossed out and not counted.
  const q = usePtSessionsListInfinite({ subscription: pt?.id }, { query: { ...paged, enabled: !!pt } });
  const { rows } = pages(q);
  const given = rows.filter((s) => !s.voided);
  const [open, setOpen] = useState<PTSession | null>(null);

  if (!m) return <Shell><SkeletonRows /></Shell>;
  if (!pt) return <Shell name={m.name}><Empty icon={Dumbbell} title="No personal training" text={`${m.name} has no personal training running.`} /></Shell>;

  const { left, over, status } = ptState(pt, today);
  const pace = ptPace(pt, today);
  const worked = partCounts(given);
  const last = given[0];
  // Numbered from the first given, so the newest is No. sessions_used; removed ones take no number.
  let n = pt.sessions_used + 1;
  const numbered = rows.map((s) => ({ s, no: s.voided ? null : --n }));
  return (
    <Shell name={m.name}>
      <Section>
        <div className={`rl-pass${over ? " rl-pass--expired" : status === "expiring" ? " rl-pass--renew" : ""}`}>
          <div className="rl-pass__top"><Status status={status} /><span className="rl-pass__plan">{pt.name}</span></div>
          <p className="rl-figure">{left} <small>{left === 1 ? "session left" : "sessions left"}</small></p>
          <Bar used={pt.sessions_used} total={pt.sessions} label={sessionsUsed(pt)} />
          <div className="rl-pass__dates"><span>{day(pt.starts)}</span><span>{pt.ends < today ? "Ended" : "Ends"} {day(pt.ends)}</span></div>
        </div>
      </Section>
      <Section title="Details">
        <Details rows={[
          { icon: UserRound, label: "Trainer", value: pt.trainer_name },
          { icon: CalendarDays, label: "Runs", value: `${day(pt.starts)} to ${day(pt.ends)}` },
          { icon: CircleCheck, label: "Sessions", value: `${sessionsUsed(pt)}, ${left} left` },
          {
            icon: Gauge, label: "Pace",
            value: `${pace.soFar} a week so far${pace.toGo && !over ? `, ${pace.toGo} to go` : ""}`,
          },
          { icon: CalendarCheck, label: "Last session", value: q.isLoading ? "…" : last ? (last.local_date === today ? "Today" : day(last.local_date)) : "None yet" },
          ...(pt.frozen_from ? [{ icon: Snowflake, label: "Frozen", value: `${day(pt.frozen_from)} to ${pt.frozen_until ? day(pt.frozen_until) : "further notice"}` }] : []),
        ]} />
      </Section>
      {worked.length > 0 && (
        <Section title="Worked most" aside={<p className="rl-section__aside">From {plural(given.length, "session")}</p>}>
          <div className="rl-card rl-card--pad">
            <ul className="rl-chips" style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {worked.map((w) => <li key={w.part} className="rl-pill">{w.part} <b>{w.count}</b></li>)}
            </ul>
          </div>
        </Section>
      )}
      <Section title="Sessions" aside={pt.sessions_used ? <p className="rl-section__aside">{plural(pt.sessions_used, "session")} given</p> : undefined}>
        {q.isLoading ? <SkeletonRows n={3} /> : rows.length ? (
          <>
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {numbered.map(({ s, no }) => (
                <li key={s.id}>
                  <button className="rl-mrow" type="button" style={{ width: "100%", textAlign: "left", background: "none", border: 0, font: "inherit" }} aria-haspopup="dialog" onClick={() => setOpen(s)}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Dumbbell} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name" style={s.voided ? { textDecoration: "line-through" } : undefined}>{s.local_date === today ? "Today" : day(s.local_date)}</span>
                    <span className="rl-row__meta rl-mrow__meta">{sessionMeta(s)}{s.notes ? ` • ${s.notes}` : ""}</span>
                    {no !== null && <span className="rl-mrow__time rl-mrow__time--muted">No. {no}</span>}
                  </button>
                </li>
              ))}
            </ul>
            <LoadMore q={q} />
          </>
        ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No sessions given yet.</p></div>}
      </Section>
      <SessionSheet session={open} member={mid} today={today} used={given.flatMap((s) => s.body_parts)} staff={role.role !== "member"}
        onChange={setOpen} onClose={() => setOpen(null)} />
    </Shell>
  );
}

function Shell({ name, children }: { name?: string; children: React.ReactNode }) {
  return (
    <div className="rl-app rl-root">
      <PageBar title="Personal training" sub={name} back />
      <main className="rl-app__main">{children}</main>
    </div>
  );
}
