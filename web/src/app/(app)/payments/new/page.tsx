"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersRetrieve } from "@/api/gen/members/members";
import type { Member, Payment } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Seg, Sheet } from "@/components/ui";
import { ActionBar, MemberCard, MemberPicker, METHODS, type Method } from "@/features/sell";
import { rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";

function CollectPayment() {
  const params = useSearchParams();
  const pre = Number(params.get("member")) || 0;
  const preQ = useMembersRetrieve(pre, { query: { enabled: !!pre } });
  const [picked, setPicked] = useState<Member | null>(null);
  const member = picked ?? (preQ.data?.data as Member | undefined) ?? null;
  const due = member?.balance_paise ?? 0;
  const [mode, setMode] = useState<"full" | "part">("full");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState<Method>("upi");
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<Payment | null>(null);
  const a = useAction();
  const paid = mode === "full" ? due : toPaise(amount);

  async function save() {
    if (!member) return setErr("Choose the member first");
    if (!due) return setErr(`${member.name} has nothing due. Add a plan first.`);
    if (paid <= 0 || paid > due) return setErr(`Enter an amount up to ${rupees(due)}`);
    try { setDone((await a.run<Payment>("/api/payments/", { member: member.id, amount_paise: paid, method, note }))!); } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Collect Payment" />
      <main className="rl-app__main">
        {member ? <MemberCard m={member} onChange={pre ? undefined : () => setPicked(null)} /> : <MemberPicker onPick={(m) => { setPicked(m); setErr(undefined); }} />}
        {member && (
          <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
            {due ? (
              <>
                <fieldset className="rl-fieldset"><legend>Amount</legend>
                  <Seg label="Amount" value={mode} onChange={setMode} options={[{ value: "full", label: "Full amount" }, { value: "part", label: "Part payment" }]} />
                  <label className="rl-amount" style={{ marginTop: "var(--space-2)" }}>
                    <span aria-hidden="true">₹</span>
                    <input type="number" inputMode="numeric" min={1} aria-label="Amount in rupees" readOnly={mode === "full"} value={mode === "full" ? due / 100 : amount} onChange={(e) => { setAmount(e.target.value); setErr(undefined); }} />
                  </label>
                  <p className="rl-field__hint">{due - paid > 0 ? `${rupees(due - paid)} stays due after this payment` : "Nothing stays due after this payment"}</p>
                </fieldset>
                <fieldset className="rl-fieldset"><legend>Paid by</legend><Choices name="method" two value={method} onChange={setMethod} options={METHODS} /></fieldset>
                <Field label="Note" optional hint="Shown on the payment record.">{(id) => <input className="rl-field__input" id={id} value={note} placeholder="UPI ref 4821" onChange={(e) => setNote(e.target.value)} />}</Field>
              </>
            ) : (
              <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>{member.name} has nothing due. <Link className="rl-link" href={`/subscriptions/new?member=${member.id}`}><span>Add a plan</span></Link></p></div>
            )}
          </form>
        )}
        <ErrorText>{err ?? a.error?.message}</ErrorText>
      </main>
      <ActionBar label={paid ? `Collect ${rupees(paid)}` : "Collect"} onClick={save} busy={a.busy} busyLabel="Collecting…" />
      <Sheet open={!!done} onClose={() => setDone(null)} closable={false}>
        {done && member && (
          <>
            <Confirm title={`${rupees(done.amount_paise)} collected`} text={`From ${member.name} by ${done.method.toUpperCase()}. ${due - done.amount_paise > 0 ? `${rupees(due - done.amount_paise)} is still due.` : "Nothing is due now."}`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/members/${member.id}`}>View Member</Link>
              <Link className="rl-button rl-button--secondary rl-button--block" href="/home">Done</Link>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><CollectPayment /></Suspense>; }
