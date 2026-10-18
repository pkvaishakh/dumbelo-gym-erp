"use client";
import { AlertCircle, CalendarDays, Hash, Inbox, MessageCircle } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { ConsoleBranchAsk } from "@/api/gen/model";
import { usePlatformBranchRequestsListInfinite, usePlatformGymsPlanRetrieve, usePlatformGymsRetrieve } from "@/api/gen/platform/platform";
import { DetailBar } from "@/components/shell";
import { Details, Empty, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { EditPlanSheet, MovePricesSheet } from "@/features/console/plan-sheets";
import { RequestRow, RequestSheet } from "@/features/console/requests";
import { BranchRoom, PlanCard, PlanPrices } from "@/features/rackline-plan";
import { day, ordinal, plural, WHATSAPP_MODE } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** A gym's Rackline plan in the Console: what it pays, its quota, billing day and WhatsApp, and its branch requests. */
export default function GymPlanScreen() {
  const { id } = useParams<{ id: string }>();
  const gymId = Number(id);
  const gym = usePlatformGymsRetrieve(gymId).data?.data;
  const q = usePlatformGymsPlanRetrieve(gymId);
  const asks = usePlatformBranchRequestsListInfinite({ gym: gymId }, { query: paged });
  const plan = q.data?.data;
  const [sheet, setSheet] = useState<"edit" | "prices" | null>(null);
  const [open, setOpen] = useState<ConsoleBranchAsk | null>(null);
  const back = `/console/gyms/${gymId}`;
  const bar = <DetailBar title={gym ? `${gym.name}: Rackline plan` : "Rackline plan"} back={back} />;
  if (q.isError) {
    return (
      <div className="rl-app rl-root">{bar}<main className="rl-app__main">
        <Empty icon={AlertCircle} title="Can't open this plan" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      </main></div>
    );
  }
  if (!plan) return <div className="rl-app rl-root">{bar}<main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  const { rows } = pages(asks);
  return (
    <div className="rl-app rl-root">
      {bar}
      <main className="rl-app__main">
        <PlanCard plan={plan} />
        <Section title="Plan">
          <BranchRoom plan={plan} />
          <div style={{ marginTop: "var(--space-3)" }}>
            <Details rows={[
              { icon: Hash, label: "Branches it has room for", value: plural(plan.branch_quota, "branch", "branches") },
              { icon: CalendarDays, label: "Billing day", value: `The ${ordinal(plan.billing_day)}, for the month ahead` },
              { icon: MessageCircle, label: "WhatsApp", value: WHATSAPP_MODE[plan.whatsapp_mode]?.label ?? plan.whatsapp_mode },
            ]} />
          </div>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" aria-haspopup="dialog" style={{ marginTop: "var(--space-3)" }} onClick={() => setSheet("edit")}>Edit Plan</button>
        </Section>
        <Section title="Prices" aside={<p className="rl-section__aside">From {day(plan.price_list.active_from)}</p>}>
          {plan.current_prices && (
            <div className="rl-card rl-card--pad" style={{ marginBottom: "var(--space-3)" }}>
              <p className="rl-row__title" style={{ margin: 0 }}>New prices since {day(plan.current_prices.active_from)}</p>
              <p className="rl-row__meta">{gym?.name ?? "This gym"} still pays the prices from {day(plan.price_list.active_from)}.</p>
              <button className="rl-button rl-button--block" type="button" aria-haspopup="dialog" onClick={() => setSheet("prices")}>Move to Current Prices</button>
            </div>
          )}
          <PlanPrices plan={plan} />
        </Section>
        <Section title="Branch requests">
          {asks.isLoading ? <SkeletonRows n={2} /> : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">{rows.map((r) => <RequestRow key={r.id} r={r} onOpen={() => setOpen(r)} />)}</ul>
              <LoadMore q={asks} />
            </>
          ) : (
            <Empty icon={Inbox} title="No requests yet" text="When its admin taps Add Branch to My Plan, the request shows here and in Requests." />
          )}
        </Section>
      </main>
      <EditPlanSheet gymId={gymId} plan={plan} open={sheet === "edit"} onClose={() => setSheet(null)} />
      <MovePricesSheet gymId={gymId} gymName={gym?.name ?? "This gym"} plan={plan} open={sheet === "prices"} onClose={() => setSheet(null)} />
      <RequestSheet r={open} onClose={() => setOpen(null)} />
    </div>
  );
}
