"use client";
/* The member's own plans (Home's membership card, More): what's running now, what's up next and what has ended, with
 * each one's money. Personal training opens its sessions. Their payments are /membership/payments. Read only. */
import { CalendarX, Dumbbell, Ticket } from "lucide-react";
import Link from "next/link";

import type { Subscription } from "@/api/gen/model";
import { useSubscriptionsListInfinite } from "@/api/gen/subscriptions/subscriptions";
import { Bar, Empty, Icon, LoadMore, PassActions, Section, SkeletonRows, Status } from "@/components/ui";
import { MemberScreen } from "@/features/my-membership";
import { owedOn, PlanMoney } from "@/features/plan-money";
import { day, daysLeft, gymToday, planDays, plural, rangeLabel, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";
import { ptState, sessionsUsed } from "@/lib/pt";
import { useSession } from "@/lib/session";
import type { MemberSelf } from "@/lib/types";

/** A membership's last week reads "Expiring", as the API has it. */
const EXPIRING_DAYS = 7;

/** A plan as sold: its dates are always set (the API only leaves them optional when selling). */
type Sold = Subscription & { starts: string; ends: string };

function MyPlans() {
  const { role } = useSession();
  return <MemberScreen title="My plans" what="plans">{(me) => <Plans me={me} today={gymToday(role.timezone)} />}</MemberScreen>;
}

/** Every plan they've bought, newest first, sorted into now, up next and ended. */
function Plans({ me, today }: { me?: MemberSelf; today: string }) {
  const q = useSubscriptionsListInfinite(undefined, { query: paged });
  const rows = pages(q).rows.map((s) => ({ ...s, starts: s.starts ?? "", ends: s.ends ?? "" }) as Sold);
  if (q.isLoading) return <SkeletonRows n={3} />;
  if (!rows.length) return <Empty icon={Ticket} title="No plans yet" text="Plans you buy at the front desk show up here." />;

  const ended = (s: Sold) => s.ends < today || (s.kind === "pt" && s.sessions_used >= s.sessions);
  const next = rows.filter((s) => !ended(s) && s.starts > today).reverse();  // the soonest first
  const now = rows.filter((s) => !ended(s) && s.starts <= today).sort((a, b) => (a.kind === b.kind ? 0 : a.kind === "pt" ? 1 : -1));
  const past = rows.filter(ended);
  return (
    <>
      <Section title="Now">
        {now.length ? (
          <div style={{ display: "grid", gap: "var(--space-3)" }}>
            {now.map((s) => <NowPass key={s.id} sub={s} me={me} today={today} />)}
          </div>
        ) : (
          <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No plan running. Renew at the front desk to check in again.</p></div>
        )}
      </Section>
      {next.length > 0 && (
        <Section title="Up next">
          <div style={{ display: "grid", gap: "var(--space-3)" }}>
            {next.map((s) => {
              const inDays = daysLeft(s.starts);
              return (
                <div key={s.id} className="rl-pass">
                  <div className="rl-pass__top">
                    <span className="rl-tag rl-tag--next">{inDays <= 0 ? "Starts today" : inDays === 1 ? "Starts tomorrow" : `Starts in ${inDays} days`}</span>
                    <span className="rl-pass__plan">{s.plan_name}</span>
                  </div>
                  <div className="rl-pass__dates"><span>{day(s.starts)}</span><span>Ends {day(s.ends)}</span></div>
                  <div className="rl-sub">
                    {s.kind === "pt" && <span><strong>Personal training:</strong> {plural(s.sessions, "session")}{s.trainer_name ? ` with ${s.trainer_name}` : ""}</span>}
                    <PlanMoney sub={s} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      )}
      {past.length > 0 && (
        <Section title="Ended">
          <ul className="rl-card rl-mlist rl-mlist--compact">
            {past.map((s) => {
              const due = owedOn(s);
              return (
                <li key={s.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={s.kind === "pt" ? Dumbbell : CalendarX} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{s.plan_name}</span>
                  <span className="rl-row__meta rl-mrow__meta">
                    {rangeLabel(s.starts, s.ends)}{s.kind === "pt" ? ` • ${sessionsUsed(s)}` : ""}
                  </span>
                  <span className={`rl-mrow__note${due ? " rl-mrow__note--alert" : ""}`}>{due ? `${rupees(due)} due` : rupees(s.paid_paise)}</span>
                </div></li>
              );
            })}
          </ul>
        </Section>
      )}
      <LoadMore q={q} />
    </>
  );
}

/** A plan running today: days or sessions left, its dates and money; personal training opens its sessions. */
function NowPass({ sub: s, me, today }: { sub: Sold; me?: MemberSelf; today: string }) {
  const pt = s.kind === "pt";
  const starts = s.starts;
  const frozen = !!s.frozen_from && s.frozen_from <= today && (!s.frozen_until || today <= s.frozen_until);
  const days = planDays(starts, s.ends, today);
  const state = pt ? ptState(s, today) : null;
  const status = state?.status ?? (frozen ? "frozen" : daysLeft(s.ends) <= EXPIRING_DAYS ? "expiring" : "active");
  return (
    <div className={`rl-pass${status === "expiring" ? " rl-pass--renew" : ""}`}>
      <div className="rl-pass__top"><Status status={status} /><span className="rl-pass__plan">{s.plan_name}</span></div>
      {state ? (
        <>
          <p className="rl-figure">{state.left} <small>{state.left === 1 ? "session left" : "sessions left"}</small></p>
          <Bar used={s.sessions_used} total={s.sessions} label={sessionsUsed(s)} />
        </>
      ) : (
        <>
          <p className="rl-figure">{days.left} <small>{frozen ? "days left, paused" : "days remaining"}</small></p>
          <Bar used={days.used} total={days.total} label={`${days.used} of ${days.total} days used`} />
        </>
      )}
      <div className="rl-pass__dates"><span>{day(starts)}</span><span>Ends {day(s.ends)}</span></div>
      <div className="rl-sub">
        {pt && <span><strong>Trainer:</strong> {s.trainer_name ?? "Not set"}</span>}
        {s.frozen_from && <span><strong>Frozen</strong> {day(s.frozen_from)} to {s.frozen_until ? day(s.frozen_until) : "further notice"}</span>}
        <PlanMoney sub={s} />
      </div>
      {pt && me?.pt?.id === s.id && (
        <PassActions>
          <Link className="rl-button rl-button--soft rl-button--sm" href={`/members/${me.id}/pt`}><Icon as={Dumbbell} size="sm" />View Sessions</Link>
        </PassActions>
      )}
    </div>
  );
}

export default MyPlans;
