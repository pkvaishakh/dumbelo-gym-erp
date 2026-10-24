"use client";
/* The member's own payments (Home's membership card, More): every one, newest first, with its plan and branch. The
 * API leaves out voided ones and the desk's notes. Read only. */
import { ReceiptText, Wallet } from "lucide-react";

import { usePaymentsListInfinite } from "@/api/gen/payments/payments";
import { Empty, Icon, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { MemberScreen } from "@/features/my-membership";
import { METHODS } from "@/features/sell";
import { day, plural, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** A payment as the API sends it to the member who made it (MemberPaymentSerializer): no desk notes, no voided ones. */
type MyPayment = { id: number; subscription: number | null; plan_name: string | null; amount_paise: number; method: string; branch_name: string | null; taken_by_name: string; taken_at: string };

/** Every payment they've made, newest first. */
function MyPayments() {
  return <MemberScreen title="My payments" what="payments">{() => <Payments />}</MemberScreen>;
}

/** Their payments, a page at a time. */
function Payments() {
  const q = usePaymentsListInfinite(undefined, { query: paged });
  const { rows, count } = pages(q);
  const list = rows as unknown as MyPayment[];
  const method = (m: string) => METHODS.find((x) => x.value === m)?.title ?? m;
  if (q.isLoading) return <SkeletonRows />;
  if (!list.length) return <Empty icon={Wallet} title="No payments yet" text="Payments you make at the front desk show up here." />;
  return (
    <Section title="All payments" aside={<p className="rl-section__aside">{plural(count, "payment")}</p>}>
      <ul className="rl-card rl-mlist rl-mlist--compact">
        {list.map((p) => (
          <li key={p.id}><div className="rl-mrow">
            <span className="rl-chipicon" aria-hidden="true"><Icon as={ReceiptText} size="sm" /></span>
            <span className="rl-row__title rl-mrow__name">{rupees(p.amount_paise)} by {method(p.method)}</span>
            <span className="rl-row__meta rl-mrow__meta">{[day(p.taken_at), p.plan_name, p.branch_name].filter(Boolean).join(" • ")}</span>
          </div></li>
        ))}
      </ul>
      <LoadMore q={q} />
    </Section>
  );
}

export default MyPayments;
