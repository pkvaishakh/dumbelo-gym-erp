"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Member } from "@/api/gen/model";
import { useStaffList } from "@/api/gen/staff/staff";
import { TaskBar } from "@/components/shell";
import { Chips, Choices, ErrorText, Field, Photo, Seg, Sheet, Status, Confirm } from "@/components/ui";
import { ActionBar, METHODS, PlanPicker, usePriceOf, type Method } from "@/features/sell";
import { day, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const GOALS = ["Weight loss", "Muscle gain", "General fitness", "Strength", "Endurance"];

export default function AddMember() {
  const router = useRouter();
  const { role, branch } = useSession();
  const [step, setStep] = useState(1);
  const [f, setF] = useState({ name: "", phone: "", email: "", goal: "", home_branch: branch ?? role.branches[0]?.id ?? 0, trainer: null as number | null, password: "" });
  const [plan, setPlan] = useState<number | null>(null);
  const [offer, setOffer] = useState<number | null>(null);
  const [mode, setMode] = useState<"full" | "part" | "later">("full");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState<Method>("upi");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [made, setMade] = useState<Member | null>(null);
  const price = usePriceOf(plan, offer);
  const trainers = useStaffList({ role: "trainer", is_active: true, limit: 100, branches: f.home_branch ? [f.home_branch] : undefined });
  const a = useAction();
  const paid = mode === "full" ? price.total : mode === "part" ? toPaise(amount) : 0;

  function next() {
    const e: Record<string, string> = {};
    if (step === 1) {
      if (!f.name.trim()) e.name = "Enter the member’s full name";
      if (f.phone.replace(/\D/g, "").length !== 10) e.phone = "Enter a 10-digit mobile number";
      if (f.password && f.password.length < 6) e.password = "Use at least 6 characters, or leave it empty";
    }
    if (step === 2 && !plan) e.plan = "Choose a plan";
    if (step === 3 && mode === "part" && (paid <= 0 || paid >= price.total)) e.amount = `Enter less than ${rupees(price.total)}, or choose Full amount`;
    setErrs(e);
    if (Object.keys(e).length) return;
    if (step < 3) setStep(step + 1);
    else save();
  }

  async function save() {
    try {
      const m = await a.run<Member>("/api/members/", {
        name: f.name.trim(), phone: f.phone, email: f.email.trim(), goal: f.goal, home_branch: f.home_branch, trainer: f.trainer,
        first_plan: plan, offer, ...(paid ? { paid_paise: paid, method } : {}), ...(f.password ? { password: f.password } : {}),
      });
      setMade(m!);
    } catch (err) {
      const fields = (err as { fields?: Record<string, string[]> }).fields;
      if (fields?.phone || fields?.name) { setStep(1); setErrs({ phone: fields.phone?.[0] ?? "", name: fields.name?.[0] ?? "" }); }
    }
  }

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => { setF({ ...f, [k]: e.target.value }); setErrs({ ...errs, [k]: "" }); };

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Add Member" step={[step, 3]} onClose={step > 1 ? () => setStep(step - 1) : undefined} />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); next(); }}>
          {step === 1 && (
            <>
              <Field label="Full name" error={errs.name}>{(id) => <input className="rl-field__input" id={id} autoComplete="off" autoCapitalize="words" enterKeyHint="next" placeholder="As on their ID" value={f.name} onChange={set("name")} />}</Field>
              <Field label="Mobile number" prefix="+91" error={errs.phone} hint="They sign in to the app with this number.">{(id) => <input className="rl-field__input" id={id} type="tel" inputMode="numeric" autoComplete="off" enterKeyHint="next" placeholder="10-digit number" value={f.phone} onChange={set("phone")} />}</Field>
              <Field label="Email" optional>{(id) => <input className="rl-field__input" id={id} type="email" inputMode="email" autoCapitalize="none" placeholder="name@example.com" value={f.email} onChange={set("email")} />}</Field>
              {role.branches.length > 1 && (
                <Field label="Home branch">{(id) => (
                  <select className="rl-field__input" id={id} value={f.home_branch} onChange={(e) => setF({ ...f, home_branch: Number(e.target.value), trainer: null })}>
                    {role.branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                )}</Field>
              )}
              <Field label="Trainer" optional>{(id) => (
                <select className="rl-field__input" id={id} value={f.trainer ?? ""} onChange={(e) => setF({ ...f, trainer: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">No trainer yet</option>
                  {(trainers.data?.data.results ?? []).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              )}</Field>
              <fieldset className="rl-fieldset"><legend>Goal <span className="rl-optional">(optional)</span></legend>
                <Chips name="goal" label="Goal" scroll={false} value={f.goal} onChange={(v) => setF({ ...f, goal: v === f.goal ? "" : v })} options={GOALS.map((g) => ({ value: g, label: g }))} />
              </fieldset>
              <Field label="App password" optional error={errs.password} hint="Set one now and they can check in from their phone. You can also do this later.">{(id) => <input className="rl-field__input" id={id} type="text" autoComplete="new-password" value={f.password} onChange={set("password")} />}</Field>
            </>
          )}
          {step === 2 && (
            <>
              <PlanPicker plan={plan} setPlan={(v) => { setPlan(v); setErrs({}); }} offer={offer} setOffer={setOffer} />
              <ErrorText>{errs.plan}</ErrorText>
              {price.off > 0 && <p className="rl-field__hint">{price.offer?.name}: {rupees(price.off)} off {rupees(price.list)}</p>}
            </>
          )}
          {step === 3 && (
            <>
              <fieldset className="rl-fieldset"><legend>Payment</legend>
                <Seg label="Amount" value={mode} onChange={setMode} options={[{ value: "full", label: "Full" }, { value: "part", label: "Part" }, { value: "later", label: "Later" }]} />
                {mode !== "later" && (
                  <label className="rl-amount" style={{ marginTop: "var(--space-2)" }}>
                    <span aria-hidden="true">₹</span>
                    <input type="number" inputMode="numeric" min={1} aria-label="Amount in rupees" readOnly={mode === "full"} value={mode === "full" ? price.total / 100 : amount} onChange={(e) => { setAmount(e.target.value); setErrs({}); }} />
                  </label>
                )}
                <ErrorText>{errs.amount}</ErrorText>
                <p className="rl-field__hint">{mode === "later" ? `${rupees(price.total)} stays due. The membership shows Payment due until it's paid.` : price.total - paid > 0 ? `${rupees(price.total - paid)} stays due after this payment` : "Nothing stays due after this payment"}</p>
              </fieldset>
              {mode !== "later" && (
                <fieldset className="rl-fieldset"><legend>Paid by</legend>
                  <Choices name="method" two value={method} onChange={setMethod} options={METHODS} />
                </fieldset>
              )}
              <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
            </>
          )}
        </form>
      </main>
      <ActionBar label={step < 3 ? "Continue" : paid ? `Collect ${rupees(paid)}` : "Add Member"} total={step > 1 && price.total ? rupees(price.total) : undefined} onClick={next} busy={a.busy} busyLabel="Adding…" />

      <Sheet open={!!made} onClose={() => router.push(`/members/${made!.id}`)} closable={false}>
        {made && (
          <>
            <Confirm title={`${made.name} is now a member`} text={made.balance_paise ? `${rupees(made.balance_paise)} is still due.` : "Fully paid. They can check in now."} />
            <div className="rl-idcard">
              <div className="rl-idcard__who"><Photo name={made.name} size="lg" /><span><span className="rl-row__title">{made.name}</span><span className="rl-row__meta">{made.code}</span><Status status={made.status} /></span></div>
              {made.plan && <dl className="rl-facts"><dt>Plan</dt><dd>{String((made.plan as { name: string }).name)}</dd><dt>Valid until</dt><dd>{day(String((made.plan as { ends: string }).ends))}</dd></dl>}
            </div>
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="button" onClick={() => router.push(`/members/${made.id}`)}>View Member</button>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setMade(null); setStep(1); setPlan(null); setOffer(null); setF({ ...f, name: "", phone: "", email: "", goal: "", password: "", trainer: null }); }}>Add Another</button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}
