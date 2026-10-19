"use client";
/* Changing a gym's Dumbelo invoices in the Console: Record Payment, Void Invoice or Void Payment, Add Charge, and a
 * pending charge to take back. */
import { Banknote, CalendarDays, Landmark, Receipt, Smartphone, UserRound } from "lucide-react";
import { useState } from "react";

import type { Charge, ChargeCreateKindEnum, ConsoleInvoice, ConsolePlan, DumbeloPayMethodEnum } from "@/api/gen/model";
import { Choices, Confirm, Details, ErrorText, Field, Sheet } from "@/components/ui";
import { day, isoDate, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

const REFRESH = ["/api/platform/"];

const METHODS: { value: DumbeloPayMethodEnum; title: string; icon: typeof Landmark }[] = [
  { value: "bank", title: "Bank transfer", icon: Landmark },
  { value: "upi", title: "UPI", icon: Smartphone },
  { value: "cheque", title: "Cheque", icon: Receipt },
  { value: "cash", title: "Cash", icon: Banknote },
];

/** Record Payment: all or part of what the invoice owes, never more, with the bank's reference for the receipt. */
export function RecordPaymentSheet({ inv, open, onClose }: { inv: ConsoleInvoice; open: boolean; onClose: () => void }) {
  const today = isoDate(new Date());
  const fresh = () => ({ amount: String(inv.owed_paise / 100), method: "bank" as DumbeloPayMethodEnum, reference: "", paid_on: today });
  const [f, setF] = useState(fresh);
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<ConsoleInvoice | null>(null);
  const a = useAction();
  const paise = toPaise(f.amount);
  const close = () => { setDone(null); setErr(undefined); a.clearError(); setF(fresh()); onClose(); };
  async function save() {
    if (paise <= 0) return setErr("Enter the amount");
    if (paise > inv.owed_paise) return setErr(`${inv.number} owes ${rupees(inv.owed_paise)}. Record that or less.`);
    try {
      setDone((await a.run<ConsoleInvoice>(`/api/platform/invoices/${inv.id}/payments/`, { amount_paise: paise, method: f.method, reference: f.reference.trim(), paid_on: f.paid_on }, { refresh: REFRESH }))!);
    } catch { /* shown */ }
  }
  const receipt = done?.payments.at(-1);
  return (
    <Sheet open={open} onClose={close} title={done ? undefined : `Record payment for ${inv.number}`} closable={!done}>
      {done ? (
        <>
          <Confirm title={`${rupees(receipt?.amount_paise ?? paise)} recorded`}
            text={`Receipt ${receipt?.receipt_number ?? ""}. ${done.owed_paise ? `${rupees(done.owed_paise)} is still to pay.` : `${inv.gym_name} has paid this invoice in full.`}`} />
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <fieldset className="rl-fieldset"><legend>Amount</legend>
            <label className={`rl-amount${err ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
              <input type="number" inputMode="decimal" aria-label="Amount in rupees" value={f.amount} onChange={(e) => { setF({ ...f, amount: e.target.value }); setErr(undefined); }} />
            </label>
            <ErrorText>{err ?? fieldError(a.error, "amount_paise")}</ErrorText>
            {!err && paise > 0 && paise < inv.owed_paise && <p className="rl-field__hint">{rupees(inv.owed_paise - paise)} will still be owed.</p>}
          </fieldset>
          <fieldset className="rl-fieldset"><legend>Paid by</legend><Choices name="rl-pay-method" two value={f.method} onChange={(method) => setF({ ...f, method })} options={METHODS} /></fieldset>
          <Field label="Reference" optional error={fieldError(a.error, "reference")} hint="The UTR, cheque or transaction number. It goes on the receipt.">
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} maxLength={80} autoComplete="off" value={f.reference} onChange={(e) => setF({ ...f, reference: e.target.value })} />}
          </Field>
          <Field label="Date the money came in" error={fieldError(a.error, "paid_on")}>
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="date" max={today} value={f.paid_on} onChange={(e) => e.target.value && setF({ ...f, paid_on: e.target.value })} />}
          </Field>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Recording…" : paise > 0 ? `Record ${rupees(paise)}` : "Record Payment"}</button>
          </div>
        </form>
      )}
    </Sheet>
  );
}

/** Void Invoice or Void Payment: it stays, marked void with the reason. `url` is the void action to call. */
export function VoidSheet({ open, onClose, title, text, url, action }: {
  open: boolean; onClose: () => void; title: string; text: string; url: string; action: string;
}) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const close = () => { setReason(""); setErr(undefined); a.clearError(); onClose(); };
  async function save() {
    if (!reason.trim()) return setErr("Say why, for the gym's history");
    try { await a.run(url, { reason: reason.trim() }, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={title}>
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <p className="rl-row__meta" style={{ margin: 0 }}>{text}</p>
        <Field label="Why" error={err ?? fieldError(a.error, "reason")} hint="The gym's admins see this.">
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} maxLength={200} value={reason} onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}
        </Field>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Voiding…" : action}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={close}>Keep It</button>
        </div>
      </form>
    </Sheet>
  );
}

const KINDS: { value: ChargeCreateKindEnum; title: string; meta: string }[] = [
  { value: "whatsapp_setup", title: "WhatsApp setup", meta: "Once, when its WhatsApp is set up" },
  { value: "machine_setup", title: "Attendance machine setup", meta: "Once for each machine" },
  { value: "adjustment", title: "Another charge", meta: "Say what it's for" },
];

/** Add Charge: a one-time line for the gym's next invoice. Setup fees start at the gym's own prices. */
export function AddChargeSheet({ gymId, plan, open, onClose }: { gymId: number; plan: ConsolePlan; open: boolean; onClose: () => void }) {
  const priceOf = (kind: ChargeCreateKindEnum) => kind === "whatsapp_setup" ? plan.whatsapp_setup_paise : kind === "machine_setup" ? plan.machine_setup_paise : 0;
  const start = (kind: ChargeCreateKindEnum) => ({ kind, quantity: "1", amount: priceOf(kind) ? String(priceOf(kind) / 100) : "", description: "" });
  const [f, setF] = useState(() => start("whatsapp_setup"));
  const [errs, setErrs] = useState<{ amount?: string; description?: string; quantity?: string }>({});
  const a = useAction();
  const quantity = f.kind === "machine_setup" ? Number(f.quantity) : 1;
  const rate = toPaise(f.amount);
  const close = () => { setF(start("whatsapp_setup")); setErrs({}); a.clearError(); onClose(); };
  async function save() {
    const e = {
      amount: rate > 0 ? undefined : "Enter the amount",
      quantity: Number.isInteger(quantity) && quantity >= 1 && quantity <= 50 ? undefined : "Enter how many machines, 1 to 50",
      description: f.kind === "adjustment" && !f.description.trim() ? "Say what it's for, as the gym will read it" : undefined,
    };
    setErrs(e);
    if (e.amount || e.quantity || e.description) return;
    try {
      await a.run("/api/platform/charges/", { gym: gymId, kind: f.kind, quantity, rate_paise: rate, description: f.description.trim() }, { refresh: REFRESH });
      close();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Add Charge">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <fieldset className="rl-fieldset"><legend>What it is</legend>
          <Choices name="charge-kind" value={f.kind} onChange={(kind) => { setF(start(kind)); setErrs({}); }} options={KINDS} />
        </fieldset>
        {f.kind === "machine_setup" && (
          <Field label="Machines" error={errs.quantity ?? fieldError(a.error, "quantity")}>
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="text" inputMode="numeric" value={f.quantity} onChange={(e) => setF({ ...f, quantity: e.target.value.replace(/\D/g, "") })} />}
          </Field>
        )}
        <Field label={f.kind === "machine_setup" ? "Each machine" : "Amount"} prefix="₹" error={errs.amount ?? fieldError(a.error, "rate_paise")}
          hint={priceOf(f.kind) ? `Its plan's price is ${rupees(priceOf(f.kind))}.` : undefined}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="number" inputMode="decimal" value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} />}
        </Field>
        <Field label="On the invoice as" optional={f.kind !== "adjustment"} error={errs.description ?? fieldError(a.error, "description")}
          hint={f.kind === "adjustment" ? undefined : "Left empty, it says what the charge is."}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} maxLength={200} value={f.description} placeholder={f.kind === "adjustment" ? "Training day for the desk" : KINDS.find((k) => k.value === f.kind)?.title} onChange={(e) => setF({ ...f, description: e.target.value })} />}
        </Field>
        <p className="rl-row__meta" style={{ margin: 0 }}>{rate > 0 ? `${rupees(rate * (quantity || 1))} on` : "It goes on"} the gym&apos;s next invoice, written on its billing day.</p>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Adding…" : "Add Charge"}</button></div>
      </form>
    </Sheet>
  );
}

/** A charge waiting for the next invoice. One added by hand can be taken back; branches added are billed as approved. */
export function ChargeSheet({ charge, onClose }: { charge: Charge | null; onClose: () => void }) {
  const a = useAction();
  const close = () => { a.clearError(); onClose(); };
  const byHand = charge && charge.kind !== "branches_pro_rata";
  async function remove() {
    try { await a.run(`/api/platform/charges/${charge!.id}/`, undefined, { method: "DELETE", refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!charge} onClose={close} title={charge?.description}>
      {charge && (
        <>
          <Details rows={[
            { icon: Receipt, label: "On the next invoice", value: rupees(charge.amount_paise) },
            { icon: UserRound, label: byHand ? "Added by" : "Approved by", value: charge.added_by_name ?? "Dumbelo" },
            { icon: CalendarDays, label: "Added", value: day(charge.created_at) },
          ]} />
          {byHand ? (
            <>
              <ErrorText>{a.error?.message}</ErrorText>
              <div className="rl-sheet__actions">
                <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" disabled={a.busy} onClick={remove}>{a.busy ? "Taking it back…" : "Remove Charge"}</button>
              </div>
            </>
          ) : <p className="rl-row__meta">The rest of the month the branches were approved in. It&apos;s billed with the next invoice.</p>}
        </>
      )}
    </Sheet>
  );
}
