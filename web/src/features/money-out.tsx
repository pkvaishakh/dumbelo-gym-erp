"use client";
/* Money the gym pays out: the Pay sheet shared by bills and salaries, and their status badges. */
import { CalendarClock } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { ExpenseDue } from "@/api/gen/model";
import { Choices, Confirm, ErrorText, Field, Icon, Sheet } from "@/components/ui";
import { day, EXPENSE_CATEGORY, isoDate, PAY_METHOD, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";

import { METHODS, type Method } from "./sell";

/** Every list a payment out changes: the bill or payslip, expenses and their totals, and Home. */
export const PAID_OUT = ["/api/expense-dues/", "/api/payslips/", "/api/expenses/", "/api/reports/"];

/** Pay all or part of something owed: the amount (filled with what's owed), how, and the day. `url` is the pay action.
 *  `part` allows less than the full amount and says what will still be owed; a bill is paid once, in one amount. */
export function PaySheet({ open, onClose, title, owed, method, url, part, done }: {
  open: boolean; onClose: () => void; title: string; owed: number; method?: string; url: string; part?: boolean;
  done: (paise: number) => string;
}) {
  const today = isoDate(new Date());
  const [f, setF] = useState({ amount: String(owed / 100), method: (METHODS.some((m) => m.value === method) ? method : "upi") as Method, paid_on: today, note: "" });
  const [err, setErr] = useState<string>();
  const [paid, setPaid] = useState<number | null>(null);
  const a = useAction();
  const paise = toPaise(f.amount);
  const close = () => { setPaid(null); setErr(undefined); a.clearError(); setF((x) => ({ ...x, amount: String(owed / 100), note: "" })); onClose(); };
  async function pay() {
    if (paise <= 0) return setErr("Enter the amount");
    if (part && paise > owed) return setErr(`${rupees(owed)} is owed. Pay that or less.`);
    try {
      await a.run(url, { amount_paise: paise, method: f.method, paid_on: f.paid_on, note: f.note }, { refresh: PAID_OUT });
      setPaid(paise);
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={paid === null ? title : undefined} closable={paid === null}>
      {paid !== null ? (
        <>
          <Confirm title={`${rupees(paid)} paid`} text={done(paid)} />
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); pay(); }}>
          <fieldset className="rl-fieldset"><legend>Amount</legend>
            <label className={`rl-amount${err ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
              <input type="number" inputMode="decimal" aria-label="Amount in rupees" value={f.amount} onChange={(e) => { setF({ ...f, amount: e.target.value }); setErr(undefined); }} />
            </label>
            <ErrorText>{err}</ErrorText>
            {part && !err && paise > 0 && paise < owed && <p className="rl-field__hint">{rupees(owed - paise)} will still be owed.</p>}
          </fieldset>
          <fieldset className="rl-fieldset"><legend>Paid by</legend><Choices name="payout-method" two value={f.method} onChange={(v) => setF({ ...f, method: v })} options={METHODS} /></fieldset>
          <Field label="Date">{(id) => <input className="rl-field__input" id={id} type="date" max={today} value={f.paid_on} onChange={(e) => e.target.value && setF({ ...f, paid_on: e.target.value })} />}</Field>
          <Field label="Note" optional>{(id) => <input className="rl-field__input" id={id} maxLength={200} value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} />}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Paying…" : paise > 0 ? `Pay ${rupees(paise)}` : "Pay"}</button>
          </div>
        </form>
      )}
    </Sheet>
  );
}

const BILL: Record<string, [string, string]> = {
  overdue: ["Overdue", "expired"], today: ["Due today", "expiring"], soon: ["Due soon", "expiring"], later: ["Coming up", "frozen"],
  paid: ["Paid", "active"], skipped: ["Skipped", "frozen"],
};

/** A bill's state as a badge: the colour and the word together. */
export function BillStatus({ state }: { state: string }) {
  const [label, cls] = BILL[state] ?? [state, "frozen"];
  return <span className={`rl-status rl-status--${cls}`}>{label}</span>;
}

/** A payslip's state: a draft, or approved and how much of it is paid. */
export function PayslipStatus({ status, payment }: { status: string; payment: string }) {
  if (payment === "paid") return <span className="rl-status rl-status--active">Paid</span>;
  if (payment === "part") return <span className="rl-status rl-status--due">Part paid</span>;
  if (status === "draft") return <span className="rl-status rl-status--frozen">Draft</span>;  // a calm grey: red is for errors
  return <span className="rl-status rl-status--due">To pay</span>;
}

/** One bill: what and when, then Pay (opens the pay sheet) or Skip. Paid and skipped bills only show their facts. */
export function DueSheet({ due, onClose, record = true }: { due: ExpenseDue; onClose: () => void; record?: boolean }) {
  const [paying, setPaying] = useState(false);
  const [skipping, setSkipping] = useState(false);
  const a = useAction();
  const unpaid = due.status === "due";
  async function skip() {
    try { await a.run(`/api/expense-dues/${due.id}/skip/`, undefined, { refresh: PAID_OUT }); onClose(); } catch { /* shown */ }
  }
  if (paying) {
    return <PaySheet open onClose={onClose} title={`Pay ${due.name}`} owed={due.amount_paise} method={due.method} url={`/api/expense-dues/${due.id}/pay/`}
      done={() => `${due.name}, due ${day(due.due_on)}. It's added to ${due.branch_name}'s expenses.`} />;
  }
  return (
    <Sheet open onClose={onClose} title={skipping ? `Skip ${due.name}?` : due.name}>
      {skipping ? (
        <>
          <p className="rl-row__meta">The {day(due.due_on)} date leaves the list and nothing is spent. Use this when it won&apos;t be paid, like a month the landlord let go.</p>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={skip}>{a.busy ? "Skipping…" : "Skip It"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSkipping(false)}>Keep It</button>
          </div>
        </>
      ) : (
        <>
          <p className="rl-figure rl-sheet__figure">{rupees(due.paid_paise ?? due.amount_paise)}</p>
          <dl className="rl-details">
            {[
              ["Status", <BillStatus key="s" state={due.state} />], ["Due on", day(due.due_on)], ["Category", EXPENSE_CATEGORY[due.category] ?? due.category],
              ["Branch", due.branch_name], ["Paid to", due.paid_to || "Not added"], ["Usually paid by", PAY_METHOD[due.method] ?? due.method],
              ...(due.paid_on ? [["Paid on", day(due.paid_on)]] : []),
            ].map(([label, value]) => (
              <div className="rl-detail" key={String(label)}><span className="rl-chipicon" aria-hidden="true"><Icon as={CalendarClock} size="sm" /></span><dt>{label}</dt><dd>{value}</dd></div>
            ))}
          </dl>
          {unpaid && (
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="button" onClick={() => setPaying(true)}>Pay {rupees(due.amount_paise)}</button>
              <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setSkipping(true)}>Skip This One</button>
            </div>
          )}
          {record && <p className="rl-listmore"><Link className="rl-link" href={`/expenses/recurring/${due.recurring}`}><span>See every date</span></Link></p>}
        </>
      )}
    </Sheet>
  );
}
