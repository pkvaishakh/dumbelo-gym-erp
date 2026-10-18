"use client";
/* Refunds on a member's profile: giving money back for a plan (admins), and the refunds already given. */
import { Undo2 } from "lucide-react";
import { useState } from "react";

import type { Refund, Subscription } from "@/api/gen/model";
import { useRefundsList } from "@/api/gen/refunds/refunds";
import { useSubscriptionsList } from "@/api/gen/subscriptions/subscriptions";
import { Choices, Confirm, ErrorText, Field, Icon, Sheet, SkeletonRows } from "@/components/ui";
import { METHODS, type Method } from "@/features/sell";
import { day, gymToday, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

/** Every read a refund changes: the member, their plans and payments, the accounts, the reports. */
const REFRESH = ["/api/members/", "/api/subscriptions/", "/api/refunds/", "/api/payments/", "/api/accounts/", "/api/cash/", "/api/reports/"];

const refundable = (s: Subscription) => s.paid_paise - s.refunded_paise;
const notStarted = (s: Subscription, today: string) => (s.starts ?? today) > today;

/** What ending the plan does, in words, before anything is saved. */
function endLine(s: Subscription, left: number, today: string) {
  if (notStarted(s, today)) return `It hasn't started, so it's cancelled. Refund all ${rupees(left)} to end it.`;
  if (s.ends <= today) return "It has ended already.";
  return `Check-in stops after today: it ends today instead of ${day(s.ends)}.`;
}

export function RefundSheet({ member, name, onClose }: { member: number; name: string; onClose: () => void }) {
  const { role } = useSession();
  const today = gymToday(role.timezone);
  const subsQ = useSubscriptionsList({ member, limit: 20 });
  const subs = (subsQ.data?.data.results ?? []).filter((s) => !s.cancelled && refundable(s) > 0);
  const [pick, setPick] = useState<number | null>(null);
  const sub = subs.find((s) => s.id === pick) ?? (subs.length === 1 ? subs[0] : undefined);
  const [f, setF] = useState({ amount: "", method: "cash" as Method, end: false, reason: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState<Refund | null>(null);
  const a = useAction();
  const paise = toPaise(f.amount);
  const left = sub ? refundable(sub) : 0;

  async function save() {
    const e: Record<string, string> = {};
    if (!sub) e.plan = "Choose the plan the money was paid for";
    if (paise <= 0) e.amount = "Enter the amount to give back";
    else if (sub && paise > left) e.amount = `${rupees(left)} was paid for this plan and isn't refunded yet. Refund that or less.`;
    if (!f.reason.trim()) e.reason = "Say why, for the record";
    setErrs(e);
    if (Object.keys(e).length || !sub) return;
    try {
      const out = await a.run<Refund>("/api/refunds/", { subscription: sub.id, amount_paise: paise, method: f.method, reason: f.reason.trim(), end_plan: f.end }, { refresh: REFRESH });
      setDone(out ?? null);
    } catch { /* shown */ }
  }

  if (done) {
    return (
      <Sheet open onClose={onClose} closable={false}>
        <Confirm title={`${rupees(done.amount_paise)} refunded`}
          text={`To ${name} by ${METHODS.find((m) => m.value === done.method)?.title ?? done.method}, for ${done.plan_name}.${done.cancelled_plan ? " The plan is cancelled." : done.ended_plan ? " The plan ends today." : ""} It counts as less revenue, and nothing is owed because of it.`} />
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={onClose}>Done</button></div>
      </Sheet>
    );
  }
  return (
    <Sheet open onClose={onClose} title="Refund Money">
      {subsQ.isLoading ? <SkeletonRows n={2} /> : !subs.length ? (
        <p className="rl-row__meta">Nothing {name} paid for a plan is left to refund.</p>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <fieldset className="rl-fieldset"><legend>For</legend>
            <Choices name="refund-plan" value={sub?.id ?? null} onChange={(v) => { setPick(v); setErrs({ ...errs, plan: "" }); }} options={subs.map((s) => ({
              value: s.id, title: s.plan_name, price: rupees(refundable(s)),
              meta: `${s.starts ? `${day(s.starts)} to ` : "Until "}${day(s.ends)} • Paid ${rupees(s.paid_paise)}${s.refunded_paise ? `, ${rupees(s.refunded_paise)} refunded` : ""}`,
            }))} />
            <ErrorText>{errs.plan}</ErrorText>
          </fieldset>
          <fieldset className="rl-fieldset"><legend>Amount</legend>
            <label className={`rl-amount${errs.amount ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
              <input type="number" inputMode="decimal" aria-label="Amount to refund in rupees" value={f.amount} onChange={(e) => { setF({ ...f, amount: e.target.value }); setErrs({ ...errs, amount: "" }); }} />
            </label>
            {errs.amount ? <ErrorText>{errs.amount}</ErrorText> : sub && <p className="rl-field__hint" style={{ margin: 0 }}>Up to {rupees(left)}. It comes out of the branch&apos;s cash, or its bank account for the other ways.</p>}
          </fieldset>
          <fieldset className="rl-fieldset"><legend>Given back by</legend><Choices name="refund-method" two value={f.method} onChange={(v) => setF({ ...f, method: v })} options={METHODS} /></fieldset>
          {sub && (
            <fieldset className="rl-fieldset"><legend>The plan</legend>
              <Choices name="refund-end" value={f.end ? "end" : "keep"} onChange={(v) => setF({ ...f, end: v === "end" })} options={[
                { value: "keep", title: "Keep the plan", meta: "A goodwill refund: the plan's dates stay as they are" },
                { value: "end", title: notStarted(sub, today) ? "Cancel the plan" : "End the plan today", meta: endLine(sub, left, today) },
              ]} />
            </fieldset>
          )}
          <Field label="Reason" error={errs.reason} hint="Other admins read this.">{(id, desc) => (
            <input className="rl-field__input" id={id} aria-describedby={desc} maxLength={200} placeholder="Moving to another city" value={f.reason}
              onChange={(e) => { setF({ ...f, reason: e.target.value }); setErrs({ ...errs, reason: "" }); }} />
          )}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Refunding…" : paise > 0 ? `Refund ${rupees(paise)}` : "Refund Money"}</button>
          </div>
        </form>
      )}
    </Sheet>
  );
}

function VoidRefundSheet({ r, onClose }: { r: Refund; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function go() {
    if (!reason.trim()) return setErr("Say why, for the record");
    try { await a.run(`/api/refunds/${r.id}/void/`, { reason: reason.trim() }, { refresh: REFRESH }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title="Void this refund?">
      <p className="rl-row__meta">{rupees(r.amount_paise)} given back on {day(r.refunded_at)}. It stays on record, marked void, and counts as paid again{r.cancelled_plan || r.ended_plan ? "; the plan gets its dates back" : ""}.</p>
      <Field label="Reason" error={err}>{(id) => <input className="rl-field__input" id={id} value={reason} placeholder="Entered twice" onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}</Field>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Voiding…" : "Void Refund"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep Refund</button>
      </div>
    </Sheet>
  );
}

/** The refunds given to a member, under their payments. A member has few: one page is all of them. */
export function RefundRows({ member, admin }: { member: number; admin: boolean }) {
  const rows = useRefundsList({ member, limit: 20 }).data?.data.results ?? [];
  const [open, setOpen] = useState<Refund | null>(null);
  if (!rows.length) return null;
  return (
    <>
      <p className="rl-report__sub">Refunds</p>
      <ul className="rl-card rl-mlist rl-mlist--compact">
        {rows.map((r) => (
          <li key={r.id}><button className="rl-mrow" type="button" disabled={!admin || r.voided} onClick={() => setOpen(r)}>
            <span className="rl-chipicon" aria-hidden="true"><Icon as={Undo2} size="sm" /></span>
            <span className="rl-row__title rl-mrow__name" style={r.voided ? { textDecoration: "line-through" } : undefined}>−{rupees(r.amount_paise)} by {r.method.toUpperCase()}</span>
            <span className="rl-row__meta rl-mrow__meta">{day(r.refunded_at)} • {r.plan_name} • {r.reason}{r.voided ? ` • Voided: ${r.void_reason}` : r.cancelled_plan ? " • Plan cancelled" : r.ended_plan ? " • Plan ended" : ""}</span>
          </button></li>
        ))}
      </ul>
      {open && <VoidRefundSheet r={open} onClose={() => setOpen(null)} />}
    </>
  );
}
