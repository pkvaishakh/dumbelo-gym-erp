"use client";
/* A gym's Rackline plan as both its admins and the Console show it: what it costs and how many branches it has room for.
 * "Rackline plan", never just "plan": a member's plan is what they buy from the gym. */
import { Building2, CalendarDays, Cpu, MessageCircle, Receipt, Store } from "lucide-react";

import type { GymPlan } from "@/api/gen/model";
import { Details, Stat } from "@/components/ui";
import { BRANCH_ASK_STATUS, day, ordinal, plural, rupees } from "@/lib/format";

type Plan = Omit<GymPlan, "last_request">;

/** The monthly charge on the design's pass card, with the billing day and the branches in use under it. */
export function PlanCard({ plan, aside }: { plan: Plan; aside?: React.ReactNode }) {
  return (
    <section className="rl-section" aria-label="Rackline plan"><div className="rl-pass">
      <div className="rl-pass__top"><span className="rl-pass__plan">Rackline plan</span>{aside}</div>
      <p className="rl-figure">{rupees(plan.monthly_paise)} <small>a month</small></p>
      <div className="rl-pass__dates">
        <span>Billed on the {ordinal(plan.billing_day)}</span>
        <span>{plan.paid_until ? `Paid until ${day(plan.paid_until)}` : "Nothing paid yet"}</span>
      </div>
    </div></section>
  );
}

/** How full the plan is (a bar for the branches open against the quota), next to what each branch costs. */
export function BranchRoom({ plan }: { plan: Plan }) {
  const free = plan.branch_quota - plan.branches_in_use;
  return (
    <div className="rl-kpis">
      <Stat icon={Building2} accent value={`${plan.branches_in_use} of ${plan.branch_quota}`} label="Branches open"
        share={plan.branch_quota ? Math.min(1, plan.branches_in_use / plan.branch_quota) : 0}
        note={free > 0 ? `Room for ${plural(free, "more branch", "more branches")}` : "Full: ask for another to open one"} />
      <Stat icon={Store} value={rupees(plan.per_branch_paise)} label="Each branch, a month" note={`${plural(plan.branch_quota, "branch", "branches")} on the plan`} />
    </div>
  );
}

/** Every price on the plan. The monthly ones make up the charge; the one-time ones are billed when the work is done. */
export function PlanPrices({ plan }: { plan: Plan }) {
  return (
    <Details rows={[
      { icon: Receipt, label: "Base fee", value: `${rupees(plan.base_paise)} a month` },
      { icon: Store, label: `Per branch, for ${plural(plan.branch_quota, "branch", "branches")}`, value: `${rupees(plan.per_branch_paise)} a month each` },
      { icon: MessageCircle, label: "WhatsApp setup", value: `${rupees(plan.whatsapp_setup_paise)} once` },
      { icon: Cpu, label: "Attendance machine setup", value: `${rupees(plan.machine_setup_paise)} once, for each machine` },
      {
        icon: MessageCircle, label: "Each message delivered from Rackline's number",
        value: `${rupees(plan.utility_message_paise)} reminders and receipts • ${rupees(plan.marketing_message_paise)} offers • ${rupees(plan.authentication_message_paise)} sign-in codes`,
      },
      { icon: CalendarDays, label: "Prices from", value: day(plan.price_list.active_from) },
    ]} />
  );
}

export function AskStatus({ status }: { status: string }) {
  const s = BRANCH_ASK_STATUS[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

/** What approving a request charged: the rest of the billing month it was approved in. */
export function proRataText(r: { pro_rata_paise: number | null; days_charged: number | null; period_days: number | null; charged_from: string | null; charged_to: string | null }) {
  if (r.pro_rata_paise === null || !r.charged_from || !r.charged_to) return "";
  return `${rupees(r.pro_rata_paise)} for ${day(r.charged_from)} to ${day(r.charged_to)} (${r.days_charged} of ${r.period_days} days), on the next invoice`;
}
