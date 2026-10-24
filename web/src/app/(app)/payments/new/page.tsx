"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersRetrieve } from "@/api/gen/members/members";
import type { Member, Payment } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Seg, Sheet } from "@/components/ui";
import { ActionBar, backTo, MemberCard, MemberPicker, METHODS, type Method } from "@/features/sell";
import { rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";

const METHOD_NAME: Record<string, string> = Object.fromEntries(METHODS.map((m) => [m.value, m.title]));

function CollectPayment() {
  const params = useSearchParams();
  const pre = Number(params.get("member")) || 0;
  const fromMember = params.get("back") === "member"; // opened from the member's page: finishing goes back there
  const router = useRouter();
  const preQ = useMembersRetrieve(pre, { query: { enabled: !!pre } });
  const [picked, setPicked] = useState<Member | null>(null);
  const member = picked ?? (preQ.data?.data as Member | undefined) ?? null;
  const due = member?.balance_paise ?? 0;
  const [mode, setMode] = useState<"full" | "part">("full");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState<Method>("upi");
  const [split, setSplit] = useState(false); // paid more than one way: an amount for each
  const [shares, setShares] = useState<Partial<Record<Method, string>>>({});
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<Payment[] | null>(null);
  const [dueBefore, setDueBefore] = useState(0); // the member reloads after paying: what was due when this was taken
  const a = useAction();
  const paid = mode === "full" ? due : toPaise(amount);
  const parts = METHODS.map((m) => ({ method: m.value, amount_paise: toPaise(shares[m.value] ?? "") })).filter((p) => p.amount_paise > 0);
  const shared = parts.reduce((t, p) => t + p.amount_paise, 0);

  async function save() {
    if (!member) return setErr("Choose the member first");
    if (!due) return setErr(`${member.name} has nothing due. Add a plan first.`);
    if (paid <= 0 || paid > due) return setErr(`Enter an amount up to ${rupees(due)}`);
    if (split && parts.length < 2) return setErr("Enter an amount for two ways of paying or more");
    if (split && shared !== paid) return setErr(`The parts add up to ${rupees(shared)}. Make them ${rupees(paid)}.`);
    setDueBefore(due);
    try {
      setDone(split
        ? (await a.run<Payment[]>("/api/payments/split/", { member: member.id, parts, note }))!
        : [(await a.run<Payment>("/api/payments/", { member: member.id, amount_paise: paid, method, note }))!]);
    } catch { /* shown */ }
  }
  const total = done?.reduce((t, p) => t + p.amount_paise, 0) ?? 0;
  const how = done?.map((p) => `${rupees(p.amount_paise)} by ${METHOD_NAME[p.method] ?? p.method}`).join(" and ");

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
                <fieldset className="rl-fieldset"><legend>Paid by</legend>
                  <Seg label="Paid by" value={split ? "split" : "one"} onChange={(v) => { setSplit(v === "split"); setErr(undefined); }}
                    options={[{ value: "one", label: "One way" }, { value: "split", label: "Split payment" }]} />
                  {split ? (
                    <>
                      <div className="rl-pair">
                        {METHODS.map((m) => (
                          <Field key={m.value} label={m.title} prefix="₹">{(id) => (
                            <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={0} placeholder="0" value={shares[m.value] ?? ""}
                              onChange={(e) => { setShares({ ...shares, [m.value]: e.target.value }); setErr(undefined); }} />
                          )}</Field>
                        ))}
                      </div>
                      <p className="rl-field__hint">
                        {shared === paid ? `${parts.map((p) => rupees(p.amount_paise)).join(" + ")} = ${rupees(paid)}` : shared < paid ? `${rupees(paid - shared)} left to split` : `${rupees(shared - paid)} more than ${rupees(paid)}`}
                      </p>
                    </>
                  ) : <Choices name="method" two value={method} onChange={setMethod} options={METHODS} />}
                </fieldset>
                <Field label="Note" optional hint="Shown on the payment record.">{(id) => <input className="rl-field__input" id={id} value={note} placeholder="UPI ref 4821" onChange={(e) => setNote(e.target.value)} />}</Field>
              </>
            ) : (
              <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>{member.name} has nothing due. <Link className="rl-link" href={`/subscriptions/new?member=${member.id}${fromMember ? "&back=member" : ""}`} replace={fromMember}><span>Add a plan</span></Link></p></div>
            )}
          </form>
        )}
        <ErrorText>{err ?? a.error?.message}</ErrorText>
      </main>
      <ActionBar label={paid ? `Collect ${rupees(paid)}` : "Collect"} onClick={save} busy={a.busy} busyLabel="Collecting…" />
      <Sheet open={!!done} onClose={() => setDone(null)} closable={false}>
        {done && member && (
          <>
            <Confirm title={`${rupees(total)} collected`} text={`From ${member.name}: ${how}. ${dueBefore - total > 0 ? `${rupees(dueBefore - total)} is still due.` : "Nothing is due now."}`} />
            <div className="rl-sheet__actions">
              {fromMember ? (
                <button className="rl-button rl-button--block" type="button" onClick={() => backTo(router, `/members/${member.id}`)}>Done</button>
              ) : (
                <>
                  <Link className="rl-button rl-button--block" href={`/members/${member.id}`}>View Member</Link>
                  <Link className="rl-button rl-button--secondary rl-button--block" href="/home">Done</Link>
                </>
              )}
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><CollectPayment /></Suspense>; }
