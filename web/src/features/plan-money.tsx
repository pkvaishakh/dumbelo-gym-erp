/* A plan's money on a pass: the member's profile (the desk) and the member's own My Membership. */
import type { Subscription } from "@/api/gen/model";
import { rupees } from "@/lib/format";

import { METHODS } from "./sell";

/** How a plan was paid: " by UPI" for one way, " (Cash ₹500 + UPI ₹500)" for a split. */
function paidBy(sub: Subscription) {
  const name = (m: string) => METHODS.find((x) => x.value === m)?.title ?? m;
  if (sub.paid_by.length === 1) return ` by ${name(sub.paid_by[0]!.method)}`;
  return sub.paid_by.length ? ` (${sub.paid_by.map((p) => `${name(p.method)} ${rupees(p.amount_paise)}`).join(" + ")})` : "";
}

/** What's still to pay on one plan. */
export const owedOn = (sub: Subscription) => Math.max(0, sub.price_paise - sub.paid_paise);

/** One plan's money, for a pass: its price and offer, what's been paid and how, refunds, and what's still due. */
export function PlanMoney({ sub }: { sub: Subscription }) {
  const due = owedOn(sub);
  return (
    <>
      <span><strong>Price:</strong> {rupees(sub.price_paise)}{sub.offer_name ? ` with ${sub.offer_name} (was ${rupees(sub.list_price_paise)})` : ""}</span>
      <span><strong>Paid:</strong> {sub.paid_paise ? <>{rupees(sub.paid_paise)}{due ? ` of ${rupees(sub.price_paise)}` : " in full"}{paidBy(sub)}</> : "Nothing yet"}</span>
      {sub.refunded_paise > 0 && <span><strong>Refunded:</strong> {rupees(sub.refunded_paise)}</span>}
      {due > 0 && <span><strong>Payment due:</strong> {rupees(due)}</span>}
    </>
  );
}
