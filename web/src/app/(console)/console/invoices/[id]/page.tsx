"use client";
import { AlertCircle, Printer, Receipt, UserRound } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { ConsoleInvoicePayment } from "@/api/gen/model";
import { usePlatformInvoicesRetrieve } from "@/api/gen/platform/platform";
import { DetailBar } from "@/components/shell";
import { Details, Empty, Icon, Section, Sheet, SkeletonRows } from "@/components/ui";
import { RecordPaymentSheet, VoidSheet } from "@/features/console/invoice-sheets";
import { InvoiceCard, InvoiceLines, PaymentRows } from "@/features/rackline-invoices";
import { day, RACKLINE_PAY_METHOD, rupees } from "@/lib/format";

/** One gym's Rackline invoice in the Console: Record Payment, each payment's receipt and Void Payment, Void Invoice. */
export default function ConsoleInvoiceScreen() {
  const { id } = useParams<{ id: string }>();
  const q = usePlatformInvoicesRetrieve(Number(id));
  const inv = q.data?.data;
  const [sheet, setSheet] = useState<"pay" | "void" | null>(null);
  const [open, setOpen] = useState<ConsoleInvoicePayment | null>(null);
  const [voiding, setVoiding] = useState<ConsoleInvoicePayment | null>(null);
  const back = inv ? `/console/gyms/${inv.gym}/invoices` : "/console";
  const bar = (
    <DetailBar title={inv ? `${inv.gym_name}: invoice` : "Invoice"} back={back}
      action={inv && <Link className="rl-iconbtn rl-iconbtn--plain" href={`/console/invoices/${id}/print`} aria-label="Print Invoice"><Icon as={Printer} /></Link>} />
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
  if (!inv) return <div className="rl-app rl-root">{bar}<main className="rl-app__main"><SkeletonRows n={5} /></main></div>;
  const live = inv.payments.some((p) => !p.voided);
  return (
    <div className="rl-app rl-root">
      {bar}
      <main className="rl-app__main">
        <InvoiceCard inv={inv} />
        {inv.status === "void" && (
          <div className="rl-card rl-card--pad">
            <p className="rl-row__title" style={{ margin: 0 }}>Voided{inv.voided_by_name ? ` by ${inv.voided_by_name}` : ""}{inv.voided_at ? `, ${day(inv.voided_at)}` : ""}</p>
            <p className="rl-row__meta" style={{ marginBottom: 0 }}>{inv.void_reason}</p>
          </div>
        )}
        <InvoiceLines inv={inv} />
        <Section title="Payments">
          <PaymentRows payments={inv.payments} onOpen={(p) => setOpen(inv.payments.find((x) => x.id === p.id) ?? null)} />
        </Section>
        {inv.status !== "void" && (
          <Section label="Actions">
            <div className="rl-sheet__actions" style={{ marginTop: 0 }}>
              {inv.status === "open" && <button className="rl-button rl-button--block" type="button" aria-haspopup="dialog" onClick={() => setSheet("pay")}>Record Payment</button>}
              {!live && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" aria-haspopup="dialog" onClick={() => setSheet("void")}>Void Invoice</button>}
            </div>
            {live && <p className="rl-field__hint">To void this invoice, void its payments first: tap a payment above.</p>}
          </Section>
        )}
      </main>
      <RecordPaymentSheet inv={inv} open={sheet === "pay"} onClose={() => setSheet(null)} />
      <VoidSheet open={sheet === "void"} onClose={() => setSheet(null)} title={`Void ${inv.number}?`} url={`/api/platform/invoices/${inv.id}/void/`} action="Void Invoice"
        text={`It stays in ${inv.gym_name}'s history, marked void, and they owe nothing on it. Nothing on it is billed again by itself: Add Charge bills what should be.`} />
      <PaymentSheet p={open} invoiceId={inv.id} onClose={() => setOpen(null)} onVoid={(p) => { setOpen(null); setVoiding(p); }} />
      <VoidSheet open={!!voiding} onClose={() => setVoiding(null)} title={voiding ? `Void ${rupees(voiding.amount_paise)} from ${day(voiding.paid_on)}?` : ""}
        url={voiding ? `/api/platform/invoice-payments/${voiding.id}/void/` : ""} action="Void Payment"
        text="Do this for money that never came in, like a bounced transfer. The payment stays on the invoice, marked void, and the invoice owes it again." />
    </div>
  );
}

/** A payment: who recorded it, its receipt, and Void Payment. */
function PaymentSheet({ p, invoiceId, onClose, onVoid }: { p: ConsoleInvoicePayment | null; invoiceId: number; onClose: () => void; onVoid: (p: ConsoleInvoicePayment) => void }) {
  return (
    <Sheet open={!!p} onClose={onClose} title={p ? `${rupees(p.amount_paise)}, ${day(p.paid_on)}` : undefined}>
      {p && (
        <>
          <Details rows={[
            { icon: Receipt, label: `Receipt ${p.receipt_number}`, value: `${RACKLINE_PAY_METHOD[p.method] ?? p.method}${p.reference ? `, ${p.reference}` : ""}` },
            { icon: UserRound, label: "Recorded by", value: `${p.recorded_by_name}, ${day(p.created_at)}` },
            ...(p.voided ? [{ icon: AlertCircle, label: `Voided by ${p.voided_by_name ?? "Rackline"}${p.voided_at ? `, ${day(p.voided_at)}` : ""}`, value: p.void_reason }] : []),
          ]} />
          <div className="rl-sheet__actions">
            <Link className="rl-button rl-button--secondary rl-button--block" href={`/console/invoices/${invoiceId}/receipts/${p.id}`}><Icon as={Printer} size="sm" />Print Receipt</Link>
            {!p.voided && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => onVoid(p)}>Void Payment</button>}
          </div>
        </>
      )}
    </Sheet>
  );
}
