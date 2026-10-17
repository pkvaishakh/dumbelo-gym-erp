"use client";
import Link from "next/link";
import { useState } from "react";

import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { ActionBar, METHODS, type Method } from "@/features/sell";
import { isoDate, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const CATS = ["rent", "salaries", "utilities", "equipment", "maintenance", "supplies", "marketing", "other"];

export default function AddExpense() {
  const { role, branch } = useSession();
  const [f, setF] = useState({ branch: branch ?? role.branches[0]?.id ?? 0, category: "", amount: "", method: "upi" as Method, paid_to: "", note: "", spent_on: isoDate(new Date()) });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);
  const a = useAction();
  async function save() {
    const e: Record<string, string> = {};
    if (!f.category) e.category = "Choose what it was for";
    if (toPaise(f.amount) <= 0) e.amount = "Enter the amount";
    setErrs(e);
    if (Object.keys(e).length) return;
    try { await a.run("/api/expenses/", { ...f, amount_paise: toPaise(f.amount) }, { refresh: ["/api/expenses/", "/api/reports/"] }); setDone(true); } catch { /* shown */ }
  }
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Add Expense" />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <fieldset className="rl-fieldset"><legend>Amount</legend>
            <label className="rl-amount"><span aria-hidden="true">₹</span><input type="number" inputMode="numeric" aria-label="Amount in rupees" value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} /></label>
            <ErrorText>{errs.amount}</ErrorText>
          </fieldset>
          <fieldset className="rl-fieldset"><legend>For</legend>
            <div className="rl-chips">{CATS.map((c) => <label className="rl-chipopt" key={c}><input type="radio" name="cat" checked={f.category === c} onChange={() => setF({ ...f, category: c })} /><span>{c[0]!.toUpperCase() + c.slice(1)}</span></label>)}</div>
            <ErrorText>{errs.category}</ErrorText>
          </fieldset>
          {/* The desk adds expenses for the branch it's working in; only admins pick one. */}
          {role.role === "admin" && <Field label="Branch">{(id) => <select className="rl-field__input" id={id} value={f.branch} onChange={(e) => setF({ ...f, branch: Number(e.target.value) })}>{role.branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select>}</Field>}
          <Field label="Paid to" optional>{(id) => <input className="rl-field__input" id={id} value={f.paid_to} placeholder="BESCOM" onChange={(e) => setF({ ...f, paid_to: e.target.value })} />}</Field>
          <Field label="Date">{(id) => <input className="rl-field__input" id={id} type="date" max={isoDate(new Date())} value={f.spent_on} onChange={(e) => setF({ ...f, spent_on: e.target.value })} />}</Field>
          <fieldset className="rl-fieldset"><legend>Paid by</legend><Choices name="method" two value={f.method} onChange={(v) => setF({ ...f, method: v })} options={METHODS} /></fieldset>
          <Field label="Note" optional>{(id) => <input className="rl-field__input" id={id} value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} />}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
        </form>
      </main>
      <ActionBar label={toPaise(f.amount) ? `Add ${rupees(toPaise(f.amount))}` : "Add Expense"} onClick={save} busy={a.busy} />
      <Sheet open={done} onClose={() => {}} closable={false}>
        <Confirm title="Expense added" text={`${rupees(toPaise(f.amount))} for ${f.category}, ${role.branches.find((b) => b.id === f.branch)?.name}.`} />
        <div className="rl-sheet__actions">
          <Link className="rl-button rl-button--block" href="/expenses">Done</Link>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setDone(false); setF({ ...f, amount: "", category: "", paid_to: "", note: "" }); }}>Add Another</button>
        </div>
      </Sheet>
    </div>
  );
}
