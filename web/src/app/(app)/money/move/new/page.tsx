"use client";
import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useAccountsList } from "@/api/gen/accounts/accounts";
import type { MoneyMove } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { MONEY } from "@/features/money";
import { ActionBar } from "@/features/sell";
import { gymToday, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

type Kind = "transfer" | "deposit" | "withdrawal";
const KINDS = [
  { value: "transfer" as Kind, title: "Move between accounts", meta: "Cash to bank, bank to cash, or one branch to another", icon: ArrowRightLeft },
  { value: "deposit" as Kind, title: "Put money in", meta: "From outside the gym, like the owner adding funds", icon: ArrowDownToLine },
  { value: "withdrawal" as Kind, title: "Take money out", meta: "Not an expense: the owner's drawings, bank charges", icon: ArrowUpFromLine },
];
const VERB: Record<Kind, [string, string]> = { transfer: ["Move", "moved"], deposit: ["Deposit", "deposited"], withdrawal: ["Withdraw", "withdrawn"] };

function MoveMoney() {
  const start = Number(useSearchParams().get("account")) || 0;
  const accounts = useAccountsList({ is_active: true }).data?.data ?? [];
  const today = gymToday(useSession().role.timezone); // the API refuses a day after the gym's today
  const [f, setF] = useState({ kind: "transfer" as Kind, from: start, to: 0, amount: "", moved_on: today, note: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState<MoneyMove | null>(null);
  const a = useAction();
  const needsFrom = f.kind !== "deposit";
  const needsTo = f.kind !== "withdrawal";
  const from = accounts.find((x) => x.id === f.from);
  const paise = toPaise(f.amount);
  const err = (k: string) => errs[k] || fieldError(a.error, k === "from" ? "from_account" : k === "to" ? "to_account" : k === "amount" ? "amount_paise" : k);
  const pick = (k: "from" | "to") => (e: React.ChangeEvent<HTMLSelectElement>) => { setF({ ...f, [k]: Number(e.target.value) }); setErrs({ ...errs, [k]: "" }); };
  const option = (x: (typeof accounts)[number]) => <option key={x.id} value={x.id}>{x.label} • {rupees(x.balance_paise)}</option>;

  async function save() {
    const e: Record<string, string> = {};
    if (needsFrom && !f.from) e.from = "Choose where the money comes from";
    if (needsTo && !f.to) e.to = "Choose where the money goes";
    if (needsFrom && needsTo && f.from && f.from === f.to) e.to = "Pick two different accounts";
    if (paise <= 0) e.amount = "Enter the amount";
    else if (needsFrom && from && paise > from.balance_paise) e.amount = `${from.label} holds ${rupees(Math.max(from.balance_paise, 0))}. Move that or less.`;
    setErrs(e);
    if (Object.keys(e).length) return;
    try {
      const out = await a.run<MoneyMove>("/api/money-moves/", {
        kind: f.kind, amount_paise: paise, moved_on: f.moved_on, note: f.note.trim(),
        from_account: needsFrom ? f.from : null, to_account: needsTo ? f.to : null,
      }, { refresh: MONEY });
      setDone(out ?? null);
    } catch { /* shown */ }
  }

  const [verb, past] = VERB[f.kind];
  const back = start ? `/money/accounts/${start}` : "/money";
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Move Money" />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <fieldset className="rl-fieldset"><legend>What&apos;s happening</legend>
            <Choices name="move-kind" value={f.kind} onChange={(v) => { setF({ ...f, kind: v }); setErrs({}); a.clearError(); }} options={KINDS} />
            {f.kind === "withdrawal" && <p className="rl-field__hint">Paying a bill, a supplier or a salary? Add it as an expense instead, so it shows in your spending.</p>}
          </fieldset>
          {needsFrom && (
            <Field label="From" error={err("from")}>{(id, desc) => (
              <select className="rl-field__input" id={id} aria-describedby={desc} value={f.from} onChange={pick("from")}>
                <option value={0} disabled>Choose an account</option>{accounts.map(option)}
              </select>
            )}</Field>
          )}
          {needsTo && (
            <Field label="To" error={err("to")}>{(id, desc) => (
              <select className="rl-field__input" id={id} aria-describedby={desc} value={f.to} onChange={pick("to")}>
                <option value={0} disabled>Choose an account</option>{accounts.filter((x) => !needsFrom || x.id !== f.from).map(option)}
              </select>
            )}</Field>
          )}
          <fieldset className="rl-fieldset"><legend>Amount</legend>
            <label className={`rl-amount${err("amount") ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
              <input type="number" inputMode="decimal" aria-label="Amount in rupees" value={f.amount} onChange={(e) => { setF({ ...f, amount: e.target.value }); setErrs({ ...errs, amount: "" }); }} />
            </label>
            {err("amount") ? <ErrorText>{err("amount")}</ErrorText> : needsFrom && from
              ? <p className="rl-field__hint">{from.label} holds {rupees(from.balance_paise)}{paise > 0 && paise <= from.balance_paise ? `, ${rupees(from.balance_paise - paise)} after this` : ""}.</p> : null}
          </fieldset>
          <Field label="Date" error={err("moved_on")}>{(id, desc) => (
            <input className="rl-field__input" id={id} type="date" max={today} aria-describedby={desc} value={f.moved_on} onChange={(e) => e.target.value && setF({ ...f, moved_on: e.target.value })} />
          )}</Field>
          <Field label="Note" optional hint="Why, or who did it: other admins read this.">{(id) => (
            <input className="rl-field__input" id={id} maxLength={200} placeholder="Banked the week's cash" value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} />
          )}</Field>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label={paise > 0 ? `${verb} ${rupees(paise)}` : verb === "Move" ? "Move Money" : verb} onClick={save} busy={a.busy} busyLabel="Saving…" />
      <Sheet open={!!done} onClose={() => {}} closable={false}>
        {done && (
          <>
            <Confirm title={`${rupees(done.amount_paise)} ${past}`}
              text={`${[done.from_name && `From ${done.from_name}`, done.to_name && `${done.from_name ? "to" : "Into"} ${done.to_name}`].filter(Boolean).join(" ")}. It isn't counted as income or spending.`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={back}>Done</Link>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setDone(null); setF({ ...f, amount: "", note: "" }); }}>Move More</button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><MoveMoney /></Suspense>; }
