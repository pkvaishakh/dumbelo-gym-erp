"use client";
/* Add Recurring Expense and Edit Recurring Expense: one task, the edit filled in (the design's Edit… rule). */
import Link from "next/link";
import { useRef, useState } from "react";

import type { RecurringExpense } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { day, EXPENSE_CATEGORY, FREQUENCY, isoDate, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

import { ActionBar, METHODS, type Method } from "./sell";

const FREQUENCIES = Object.entries(FREQUENCY).map(([value, title]) => ({ value, title }));

export function RecurringForm({ rule }: { rule?: RecurringExpense }) {
  const { role, branch } = useSession();
  const editing = !!rule;
  const [f, setF] = useState({
    name: rule?.name ?? "", category: rule?.category ?? "", amount: rule ? String(rule.amount_paise / 100) : "", method: (rule?.method ?? "bank") as Method,
    paid_to: rule?.paid_to ?? "", note: rule?.note ?? "", frequency: rule?.frequency ?? "monthly", starts: rule?.starts ?? isoDate(new Date()),
    ends: rule?.ends ?? "", remind_days: String(rule?.remind_days ?? 3), branch: rule?.branch ?? branch ?? role.branches[0]?.id ?? 0,
  });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);
  const a = useAction();
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => { setF({ ...f, [k]: e.target.value }); setErrs({ ...errs, [k]: "" }); };
  const err = (k: string) => errs[k] || fieldError(a.error, k === "amount" ? "amount_paise" : k);

  async function save() {
    const e: Record<string, string> = {};
    if (!f.name.trim()) e.name = "Say what it is, like Rent or Electricity";
    if (!f.category) e.category = "Choose what it's for";
    if (toPaise(f.amount) <= 0) e.amount = "Enter what it usually costs";
    if (f.ends && f.ends < f.starts) e.ends = "Pick an end date on or after the first date it's due";
    const remind = Number(f.remind_days);
    if (!Number.isInteger(remind) || remind < 0 || remind > 30) e.remind_days = "Use 0 to 30 days";
    setErrs(e);
    if (Object.keys(e).length) { if (e.name) nameRef.current?.focus(); return; }
    const body = { ...f, name: f.name.trim(), amount_paise: toPaise(f.amount), remind_days: remind, ends: f.ends || null };
    try {
      await a.run(editing ? `/api/recurring-expenses/${rule!.id}/` : "/api/recurring-expenses/", body,
        { method: editing ? "PATCH" : "POST", refresh: ["/api/recurring-expenses/", "/api/expense-dues/", "/api/reports/"] });
      setDone(true);
    } catch { /* shown */ }
  }

  const branchName = role.branches.find((b) => b.id === f.branch)?.name;
  // Once its dates are written the schedule is fixed: the API refuses a change, so the form doesn't offer one.
  const fixed = !!rule?.dates_fixed;
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={editing ? "Edit Recurring Expense" : "Add Recurring Expense"} />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Name" error={err("name")}>{(id, desc) => <input ref={nameRef} className="rl-field__input" id={id} aria-describedby={desc} maxLength={80} placeholder="Rent" enterKeyHint="next" value={f.name} onChange={set("name")} />}</Field>
          <fieldset className="rl-fieldset"><legend>Usual amount</legend>
            <label className={`rl-amount${err("amount") ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span><input type="number" inputMode="decimal" aria-label="Usual amount in rupees" value={f.amount} onChange={set("amount")} /></label>
            {err("amount") ? <ErrorText>{err("amount")}</ErrorText> : <p className="rl-field__hint">A bill that changes, like electricity, can be paid at a different amount each time.</p>}
          </fieldset>
          <fieldset className="rl-fieldset"><legend>For</legend>
            <div className="rl-chips">{Object.entries(EXPENSE_CATEGORY).filter(([c]) => c !== "salaries").map(([c, label]) => (
              <label className="rl-chipopt" key={c}><input type="radio" name="rec-cat" checked={f.category === c} onChange={() => { setF({ ...f, category: c as typeof f.category }); setErrs({ ...errs, category: "" }); }} /><span>{label}</span></label>
            ))}</div>
            <ErrorText>{err("category")}</ErrorText>
          </fieldset>
          <fieldset className="rl-fieldset"><legend>How often</legend>
            <Choices name="rec-freq" two value={f.frequency} onChange={(v) => !fixed && setF({ ...f, frequency: v as typeof f.frequency })} options={FREQUENCIES} />
            <ErrorText>{err("frequency")}</ErrorText>
          </fieldset>
          <Field label="First date it's due" error={err("starts")} hint={fixed ? "Its dates are set once it's due. To change them, stop this one and add a new one." : "Later dates keep the same day of the month."}>
            {(id, desc) => <input className="rl-field__input" id={id} type="date" aria-describedby={desc} disabled={fixed} value={f.starts} onChange={set("starts")} />}
          </Field>
          <Field label="Last date" optional error={err("ends")} hint="Leave it empty to keep it going.">
            {(id, desc) => <input className="rl-field__input" id={id} type="date" aria-describedby={desc} min={f.starts} value={f.ends} onChange={set("ends")} />}
          </Field>
          <Field label="Remind me this many days before" error={err("remind_days")} hint="It shows on Home and in Dues from then.">
            {(id, desc) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={0} max={30} aria-describedby={desc} value={f.remind_days} onChange={set("remind_days")} />}
          </Field>
          {role.branches.length > 1 && (
            <Field label="Branch">{(id) => <select className="rl-field__input" id={id} value={f.branch} onChange={(e) => setF({ ...f, branch: Number(e.target.value) })}>{role.branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select>}</Field>
          )}
          <fieldset className="rl-fieldset"><legend>Usually paid by</legend><Choices name="rec-method" two value={f.method} onChange={(v) => setF({ ...f, method: v })} options={METHODS} /></fieldset>
          <Field label="Paid to" optional>{(id) => <input className="rl-field__input" id={id} maxLength={120} placeholder="Landlord" value={f.paid_to} onChange={set("paid_to")} />}</Field>
          <Field label="Note" optional>{(id) => <input className="rl-field__input" id={id} maxLength={200} value={f.note} onChange={set("note")} />}</Field>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label={editing ? "Save Changes" : "Add Recurring Expense"} onClick={save} busy={a.busy} />
      <Sheet open={done} onClose={() => {}} closable={false}>
        <Confirm title={editing ? "Changes saved" : `${f.name.trim()} added`}
          text={`${rupees(toPaise(f.amount))} ${FREQUENCY[f.frequency]?.toLowerCase()}, first due ${day(f.starts)}, for ${branchName}. It shows in Dues ${f.remind_days === "0" ? "on the day" : `${f.remind_days} days before`}.`} />
        <div className="rl-sheet__actions">
          <Link className="rl-button rl-button--block" href={editing ? `/expenses/recurring/${rule!.id}` : "/expenses/recurring"}>Done</Link>
          {!editing && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setDone(false); setF({ ...f, name: "", amount: "", category: "", paid_to: "", note: "" }); }}>Add Another</button>}
        </div>
      </Sheet>
    </div>
  );
}
