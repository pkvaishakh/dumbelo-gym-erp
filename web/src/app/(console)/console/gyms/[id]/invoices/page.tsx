"use client";
import { AlertCircle, FileText, Plus, Receipt } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { Charge } from "@/api/gen/model";
import { usePlatformChargesList, usePlatformGymsPlanRetrieve, usePlatformGymsRetrieve, usePlatformInvoicesListInfinite } from "@/api/gen/platform/platform";
import { DetailBar } from "@/components/shell";
import { Empty, Icon, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { AddChargeSheet, ChargeSheet } from "@/features/console/invoice-sheets";
import { InvoiceRowLink } from "@/features/dumbelo-invoices";
import { day, ordinal, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** A gym's Dumbelo invoices in the Console: what it owes, every invoice, and the charges waiting for the next one. */
export default function GymInvoicesScreen() {
  const { id } = useParams<{ id: string }>();
  const gymId = Number(id);
  const gym = usePlatformGymsRetrieve(gymId).data?.data;
  const plan = usePlatformGymsPlanRetrieve(gymId).data?.data;
  const list = usePlatformInvoicesListInfinite({ gym: gymId }, { query: paged });
  const charges = usePlatformChargesList({ gym: gymId, limit: 100 });
  const { rows } = pages(list);
  const pending = charges.data?.data.results ?? [];
  const [adding, setAdding] = useState(false);
  const [open, setOpen] = useState<Charge | null>(null);
  return (
    <div className="rl-app rl-root">
      <DetailBar title={gym ? `${gym.name}: invoices` : "Invoices"} back={`/console/gyms/${gymId}`} />
      <main className="rl-app__main">
        {plan && (
          <section className="rl-section" aria-label="What it owes"><div className="rl-pass">
            <div className="rl-pass__top"><span className="rl-pass__plan">Owed to Dumbelo</span></div>
            <p className="rl-figure">{rupees(plan.owed_paise)}</p>
            <div className="rl-pass__dates">
              <span>Billed on the {ordinal(plan.billing_day)}</span>
              <span>{plan.paid_until ? `Paid until ${day(plan.paid_until)}` : "Nothing paid yet"}</span>
            </div>
          </div></section>
        )}
        <Section title="Invoices">
          {list.isLoading ? <SkeletonRows n={3} /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the invoices" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">{rows.map((inv) => <InvoiceRowLink key={inv.id} inv={inv} href={`/console/invoices/${inv.id}`} />)}</ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={FileText} title="No invoices yet"
              text={gym?.status === "active" ? "Its first invoice is written on its billing day, for the month ahead." : "Invoices are written for active gyms. Activate it to start billing."} />
          )}
        </Section>
        <Section title="For the next invoice">
          {charges.isLoading ? <SkeletonRows n={1} /> : pending.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {pending.map((c) => (
                <li key={c.id}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => setOpen(c)}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Receipt} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{c.description}</span>
                  <span className="rl-row__meta rl-mrow__meta">{rupees(c.amount_paise)} • Added {day(c.created_at)}</span>
                </button></li>
              ))}
            </ul>
          ) : (
            <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Nothing waiting. Setup fees and branches added during the month show here until they&apos;re billed.</p></div>
          )}
          {plan && (
            <button className="rl-button rl-button--secondary rl-button--block" type="button" aria-haspopup="dialog" style={{ marginTop: "var(--space-3)" }} onClick={() => setAdding(true)}>
              <Icon as={Plus} />Add Charge
            </button>
          )}
        </Section>
      </main>
      {plan && <AddChargeSheet gymId={gymId} plan={plan} open={adding} onClose={() => setAdding(false)} />}
      <ChargeSheet charge={open} onClose={() => setOpen(null)} />
    </div>
  );
}
