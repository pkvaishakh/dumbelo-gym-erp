"use client";
/* Changing a gym's Rackline plan in the Console: Edit Plan and Move to Current Prices. */
import { useState } from "react";

import type { ConsolePlan } from "@/api/gen/model";
import { Choices, ErrorText, Field, Sheet } from "@/components/ui";
import { day, ordinal, plural, rupees, WHATSAPP_MODE } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

const REFRESH = ["/api/platform/"];
const DAYS = Array.from({ length: 28 }, (_, i) => i + 1);
type Mode = "shared" | "own" | "off";

/** Edit Plan: the branch quota (never below the branches open), the billing day and how the gym sends WhatsApp. */
export function EditPlanSheet({ gymId, plan, open, onClose }: { gymId: number; plan: ConsolePlan; open: boolean; onClose: () => void }) {
  const fresh = () => ({ quota: String(plan.branch_quota), billing_day: plan.billing_day, whatsapp_mode: plan.whatsapp_mode as Mode });
  const [f, setF] = useState(fresh);
  const [was, setWas] = useState(false);
  const [err, setErr] = useState<string>();
  if (open !== was) { // start from what's saved each time the sheet opens
    setWas(open);
    if (open) setF(fresh());
  }
  const a = useAction();
  const close = () => { setErr(undefined); a.clearError(); onClose(); };
  async function save() {
    const quota = Number(f.quota);
    if (!Number.isInteger(quota) || quota < 1) return setErr("Enter how many branches, 1 or more");
    if (quota < plan.branches_in_use) return setErr(`${plural(plan.branches_in_use, "branch", "branches")} ${plan.branches_in_use === 1 ? "is" : "are"} open, so the plan needs room for at least that many`);
    setErr(undefined);
    try {
      await a.run(`/api/platform/gyms/${gymId}/plan/`, { branch_quota: quota, billing_day: f.billing_day, whatsapp_mode: f.whatsapp_mode }, { method: "PATCH", refresh: REFRESH });
      close();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Edit Plan">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Branches it has room for" error={err ?? fieldError(a.error, "branch_quota")}
          hint={`${plan.branches_in_use} open now. Each one adds ${rupees(plan.per_branch_paise)} a month. A request approved from Requests also charges the rest of the month.`}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="text" inputMode="numeric" value={f.quota} onChange={(e) => setF({ ...f, quota: e.target.value.replace(/\D/g, "") })} />}
        </Field>
        <Field label="Billing day" error={fieldError(a.error, "billing_day")} hint="Its invoice is written on this day each month, for the month ahead.">
          {(id, d) => (
            <select className="rl-field__input" id={id} aria-describedby={d} value={f.billing_day} onChange={(e) => setF({ ...f, billing_day: Number(e.target.value) })}>
              {DAYS.map((n) => <option key={n} value={n}>The {ordinal(n)}</option>)}
            </select>
          )}
        </Field>
        <fieldset className="rl-fieldset"><legend>WhatsApp messages</legend>
          <Choices name="wa-mode" value={f.whatsapp_mode} onChange={(whatsapp_mode) => setF({ ...f, whatsapp_mode })}
            options={(Object.keys(WHATSAPP_MODE) as Mode[]).map((m) => ({ value: m, title: WHATSAPP_MODE[m].label, meta: WHATSAPP_MODE[m].note }))} />
        </fieldset>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
      </form>
    </Sheet>
  );
}

/** Move to Current Prices: the gym's next invoice uses today's price list. Past invoices never change. */
export function MovePricesSheet({ gymId, gymName, plan, open, onClose }: { gymId: number; gymName: string; plan: ConsolePlan; open: boolean; onClose: () => void }) {
  const a = useAction();
  const close = () => { a.clearError(); onClose(); };
  async function move() {
    try { await a.run(`/api/platform/gyms/${gymId}/plan/current-prices/`, undefined, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={`Move ${gymName} to current prices?`}>
      <p className="rl-row__meta">
        {gymName} is on prices from {day(plan.price_list.active_from)}
        {plan.current_prices ? `. Its next invoice will use the prices from ${day(plan.current_prices.active_from)}` : ""}. Invoices already written don&apos;t change.
      </p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={move}>{a.busy ? "Moving…" : "Move to Current Prices"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={close}>Keep Its Prices</button>
      </div>
    </Sheet>
  );
}
