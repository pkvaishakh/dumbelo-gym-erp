"use client";
import { AlertCircle, Printer } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useBillingInvoicesRetrieve } from "@/api/gen/billing/billing";
import { DetailBar } from "@/components/shell";
import { Empty, Icon, Section, SkeletonRows } from "@/components/ui";
import { InvoiceCard, InvoiceLines, PaymentRows } from "@/features/rackline-invoices";
import { day } from "@/lib/format";

/** One Rackline invoice, for the gym's admins: what it's for, what's paid, and each payment's receipt to print. */
export default function RacklineInvoice() {
  const { id } = useParams<{ id: string }>();
  const q = useBillingInvoicesRetrieve(Number(id));
  const inv = q.data?.data;
  const bar = (
    <DetailBar title="Invoice" back="/rackline-plan"
      action={inv && <Link className="rl-iconbtn rl-iconbtn--plain" href={`/rackline-plan/invoices/${id}/print`} aria-label="Print Invoice"><Icon as={Printer} /></Link>} />
  );
  if (q.isError) {
    return (
      <div className="rl-app rl-root">{bar}<main className="rl-app__main">
        <Empty icon={AlertCircle} title="Can't open this invoice" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      </main></div>
    );
  }
  return (
    <div className="rl-app rl-root">
      {bar}
      <main className="rl-app__main">
        {!inv ? <SkeletonRows n={5} /> : (
          <>
            <InvoiceCard inv={inv} />
            {inv.status === "void" && (
              <div className="rl-card rl-card--pad">
                <p className="rl-row__title" style={{ margin: 0 }}>Rackline voided this invoice{inv.voided_at ? ` on ${day(inv.voided_at)}` : ""}</p>
                <p className="rl-row__meta" style={{ marginBottom: 0 }}>{inv.void_reason}. You don&apos;t owe anything on it.</p>
              </div>
            )}
            <InvoiceLines inv={inv} />
            <Section title="Payments">
              <PaymentRows payments={inv.payments} href={(p) => `/rackline-plan/invoices/${inv.id}/receipts/${p.id}`} />
              {inv.status === "open" && <p className="rl-field__hint">Pay by bank transfer or UPI. Rackline records the payment here and its receipt opens from it.</p>}
            </Section>
          </>
        )}
      </main>
    </div>
  );
}
