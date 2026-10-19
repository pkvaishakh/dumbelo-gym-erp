"use client";
/* A gym's Dumbelo invoices, as its admins and the Console show them: a row for the lists, one invoice's lines and
 * payments, and the invoice and receipt to print. The Console's invoice carries more (who recorded what), so these
 * take the fields both have. */
import { Banknote, FileText, Printer } from "lucide-react";
import Link from "next/link";

import type { InvoiceDetail, InvoicePayment, InvoiceRow } from "@/api/gen/model";
import { DetailBar } from "@/components/shell";
import { Icon, SkeletonRows } from "@/components/ui";
import { day, INVOICE_STATUS, invoiceState, DUMBELO_PAY_METHOD, rangeLabel, rupees } from "@/lib/format";

type Row = Pick<InvoiceRow, "number" | "period_from" | "period_to" | "status" | "overdue" | "total_paise" | "owed_paise" | "due_on">;
type Invoice = Omit<InvoiceDetail, "payments"> & { payments: readonly InvoicePayment[] };

export function InvoiceStatus({ inv }: { inv: Pick<Row, "status" | "overdue"> }) {
  const s = INVOICE_STATUS[invoiceState(inv)] ?? { label: inv.status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

/** "1 Nov to 30 Nov" (years shown when it isn't all this year). */
export const periodText = (inv: Pick<Row, "period_from" | "period_to">) => rangeLabel(inv.period_from, inv.period_to);

/** One invoice in a list: its number, the month it covers and what it comes to, or what's left of it once part is
 *  paid. `title` replaces the number (the Console's list across gyms names the gym). */
export function InvoiceRowLink({ inv, href, title }: { inv: Row; href: string; title?: string }) {
  const part = inv.status === "open" && inv.owed_paise !== inv.total_paise;
  return (
    <li><Link className="rl-mrow" href={href}>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={FileText} size="sm" /></span>
      <span className="rl-row__title rl-mrow__name">{title ?? inv.number}</span>
      <span className="rl-row__meta rl-mrow__meta">{periodText(inv)} • {part ? `${rupees(inv.owed_paise)} to pay` : rupees(inv.total_paise)}</span>
      <InvoiceStatus inv={inv} />
    </Link></li>
  );
}

/** What the invoice comes to on the design's pass card, with when it's due or how it was settled. */
export function InvoiceCard({ inv }: { inv: Invoice }) {
  const state = inv.status === "void" ? "Void" : inv.status === "paid" ? "Paid in full" : `${rupees(inv.owed_paise)} to pay`;
  return (
    <section className="rl-section" aria-label="Invoice total"><div className="rl-pass">
      <div className="rl-pass__top"><span className="rl-pass__plan">{inv.number}</span><InvoiceStatus inv={inv} /></div>
      <p className="rl-figure">{rupees(inv.total_paise)}</p>
      <div className="rl-pass__dates">
        <span>{periodText(inv)}</span>
        <span>{inv.status === "open" ? `${state}, due ${day(inv.due_on)}` : state}</span>
      </div>
    </div></section>
  );
}

/** Every line on the invoice and its total. GST shows only once Dumbelo charges it. */
export function InvoiceLines({ inv }: { inv: Invoice }) {
  return (
    <section className="rl-section" aria-label="What it's for"><div className="rl-card rl-card--pad">
      <dl className="rl-facts">
        {inv.lines.map((l) => (
          <Pair key={l.id} label={l.quantity > 1 && l.kind !== "branches_pro_rata" ? `${l.description} (${l.quantity} × ${rupees(l.rate_paise)})` : l.description} value={rupees(l.amount_paise)} />
        ))}
      </dl>
      {inv.tax_paise > 0 && <dl className="rl-facts"><Pair label="Subtotal" value={rupees(inv.subtotal_paise)} /><Pair label="GST" value={rupees(inv.tax_paise)} /></dl>}
      <p className="rl-total"><span>Total</span><span>{rupees(inv.total_paise)}</span></p>
    </div></section>
  );
}

/** The payments on an invoice, voided ones kept and marked. Each opens its receipt (`href`) or a sheet (`onOpen`). */
export function PaymentRows({ payments, href, onOpen }: { payments: readonly InvoicePayment[]; href?: (p: InvoicePayment) => string; onOpen?: (p: InvoicePayment) => void }) {
  if (!payments.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Nothing paid yet.</p></div>;
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {payments.map((p) => {
        const inner = (
          <>
            <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
            <span className="rl-row__title rl-mrow__name">{rupees(p.amount_paise)}</span>
            <span className="rl-row__meta rl-mrow__meta">
              {p.voided ? `Void: ${p.void_reason}` : `${day(p.paid_on)} • ${DUMBELO_PAY_METHOD[p.method] ?? p.method}${p.reference ? ` • ${p.reference}` : ""}`}
            </span>
            {p.voided && <span className="rl-status rl-status--off">Void</span>}
          </>
        );
        return (
          <li key={p.id}>
            {href ? <Link className="rl-mrow" href={href(p)}>{inner}</Link>
              : <button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => onOpen?.(p)}>{inner}</button>}
          </li>
        );
      })}
    </ul>
  );
}

/** A page to print or save as a PDF from the browser, like the salary slip: the bar and the button don't print. */
export function PrintFrame({ title, back, label, ready, children }: { title: string; back: string; label: string; ready: boolean; children: React.ReactNode }) {
  return (
    <div className="rl-app rl-root">
      <div className="rl-noprint"><DetailBar title={title} back={back} /></div>
      <main className="rl-app__main">
        {!ready ? <SkeletonRows n={6} /> : (
          <>
            {children}
            <section className="rl-section rl-noprint">
              <button className="rl-button rl-button--block" type="button" onClick={() => window.print()}><Icon as={Printer} size="sm" />{label}</button>
              <p className="rl-field__hint">To save it as a PDF, choose Save as PDF in the print window.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

/** The invoice on paper: who it's for, when it's due, its lines and what's been paid. */
export function InvoicePaper({ inv }: { inv: Invoice }) {
  const paid = inv.payments.filter((p) => !p.voided);
  return (
    <>
      <section className="rl-section">
        <div className="rl-card rl-card--pad">
          <p className="rl-row__meta" style={{ margin: 0 }}>Dumbelo</p>
          <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>Invoice {inv.number}</h2>
          <dl className="rl-facts">
            <dt>Billed to</dt><dd>{inv.gym_name}</dd>
            {inv.billing_email && <><dt>Email</dt><dd>{inv.billing_email}</dd></>}
            <dt>For</dt><dd>{periodText(inv)}</dd>
            <dt>Issued</dt><dd>{day(inv.issued_on)}</dd>
            <dt>Due</dt><dd>{day(inv.due_on)}</dd>
            {inv.status === "void" && <><dt>Void</dt><dd>{inv.void_reason}</dd></>}
          </dl>
        </div>
      </section>
      <InvoiceLines inv={inv} />
      {inv.status !== "void" && (
        <section className="rl-section" aria-label="Payments">
          <div className="rl-card rl-card--pad">
            <h2 className="rl-section__title" style={{ margin: 0 }}>Paid</h2>
            {paid.length ? (
              <dl className="rl-facts">
                {paid.map((p) => <Pair key={p.id} label={`${day(p.paid_on)}, receipt ${p.receipt_number}`} value={rupees(p.amount_paise)} />)}
              </dl>
            ) : <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>Nothing paid yet.</p>}
            <p className="rl-total"><span>{inv.owed_paise ? "Still to pay" : "Paid in full"}</span><span>{rupees(inv.owed_paise || inv.paid_paise)}</span></p>
          </div>
        </section>
      )}
    </>
  );
}

/** One payment's receipt on paper. A voided one says so at the top. */
export function ReceiptPaper({ inv, p }: { inv: Invoice; p: InvoicePayment }) {
  return (
    <section className="rl-section">
      <div className="rl-card rl-card--pad">
        <p className="rl-row__meta" style={{ margin: 0 }}>Dumbelo</p>
        <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>{p.voided ? "Void receipt" : "Receipt"} {p.receipt_number}</h2>
        <dl className="rl-facts">
          <dt>Received from</dt><dd>{inv.gym_name}</dd>
          <dt>Date</dt><dd>{day(p.paid_on)}</dd>
          <dt>Paid by</dt><dd>{DUMBELO_PAY_METHOD[p.method] ?? p.method}</dd>
          {p.reference && <><dt>Reference</dt><dd>{p.reference}</dd></>}
          <dt>For invoice</dt><dd>{inv.number}, {periodText(inv)}</dd>
          {p.voided && <><dt>Void</dt><dd>{p.void_reason}</dd></>}
        </dl>
        <p className="rl-total"><span>{p.voided ? "Not received" : "Received"}</span><span>{rupees(p.amount_paise)}</span></p>
        {!p.voided && <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>{inv.owed_paise ? `${rupees(inv.owed_paise)} is still to pay on this invoice.` : "This invoice is paid in full."}</p>}
      </div>
    </section>
  );
}

function Pair({ label, value }: { label: string; value: string }) {
  return <><dt>{label}</dt><dd>{value}</dd></>;
}
