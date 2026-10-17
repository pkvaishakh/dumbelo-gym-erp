"use client";
import { CalendarCheck, Clock, Minus, Plus, Wallet, X } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { PayTypeEnum, SalaryItem, SalaryRule, Staff } from "@/api/gen/model";
import { useSalaryRulesList } from "@/api/gen/salary-rules/salary-rules";
import { useStaffRetrieve } from "@/api/gen/staff/staff";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Icon, Sheet, SkeletonRows } from "@/components/ui";
import { rateText } from "@/features/payroll";
import { ActionBar } from "@/features/sell";
import { toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const TYPES: { value: PayTypeEnum; title: string; meta: string; icon: typeof Wallet }[] = [
  { value: "fixed", title: "Fixed monthly salary", meta: "The same every month", icon: Wallet },
  { value: "attendance", title: "Monthly, by days present", meta: "Less for days they don't check in", icon: CalendarCheck },
  { value: "daily", title: "By the day", meta: "A rate for each day they check in", icon: CalendarCheck },
  { value: "hourly", title: "By the hour", meta: "Their shift's hours, each day they check in", icon: Clock },
];
const RATE_LABEL: Record<PayTypeEnum, string> = { fixed: "Monthly salary", attendance: "Monthly salary", daily: "Pay for a day", hourly: "Pay for an hour" };

type Item = { kind: SalaryItem["kind"]; label: string; amount: string };

export default function SetSalary() {
  const { id } = useParams<{ id: string }>();
  const staff = useStaffRetrieve(Number(id)).data?.data;
  const rules = useSalaryRulesList({ staff: Number(id) });
  if (!staff || rules.isLoading) return <div className="rl-app rl-app--task rl-root"><TaskBar title="Set Salary" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  return <SalaryForm staff={staff} rule={rules.data?.data[0]} />;
}

function SalaryForm({ staff, rule }: { staff: Staff; rule?: SalaryRule }) {
  const { role } = useSession();
  // Admins work at every branch; others are paid from a branch they work at.
  const branches = staff.branches.length ? role.branches.filter((b) => staff.branches.includes(b.id)) : role.branches;
  const [f, setF] = useState({
    pay_type: (rule?.pay_type ?? "fixed") as PayTypeEnum, rate: rule ? String(rule.rate_paise / 100) : "",
    hours: rule && Number(rule.hours_per_day) ? String(Number(rule.hours_per_day)) : "", branch: rule?.branch ?? branches[0]?.id ?? 0,
  });
  const [items, setItems] = useState<Item[]>((rule?.items ?? []).map((i) => ({ kind: i.kind, label: i.label, amount: String(i.amount_paise / 100) })));
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);
  const a = useAction();
  const editing = !!rule;

  async function save() {
    const e: Record<string, string> = {};
    if (toPaise(f.rate) <= 0) e.rate = "Enter the amount";
    const hours = Number(f.hours);
    if (f.pay_type === "hourly" && !(hours > 0 && hours <= 24)) e.hours = "Enter the hours of their shift, like 6";
    items.forEach((it, i) => {
      if (!it.label.trim()) e[`item${i}`] = "Say what it's for";
      else if (toPaise(it.amount) <= 0) e[`item${i}`] = "Enter the amount";
    });
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = {
      staff: staff.id, branch: f.branch, pay_type: f.pay_type, rate_paise: toPaise(f.rate), hours_per_day: f.pay_type === "hourly" ? hours.toFixed(2) : "0.00",
      items: items.map((it) => ({ kind: it.kind, label: it.label.trim(), amount_paise: toPaise(it.amount) })),
    };
    try {
      await a.run(editing ? `/api/salary-rules/${rule!.id}/` : "/api/salary-rules/", body, { method: editing ? "PATCH" : "POST", refresh: ["/api/salary-rules/", "/api/payslips/"] });
      setDone(true);
    } catch { /* shown */ }
  }
  const setItem = (i: number, patch: Partial<Item>) => { setItems(items.map((it, j) => (j === i ? { ...it, ...patch } : it))); setErrs({ ...errs, [`item${i}`]: "" }); };
  const add = (kind: Item["kind"]) => setItems([...items, { kind, label: "", amount: "" }]);

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={editing ? "Change Salary" : "Set Salary"} aside={staff.name} />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <fieldset className="rl-fieldset"><legend>How {staff.name.split(" ")[0]} is paid</legend>
            <Choices name="pay-type" value={f.pay_type} onChange={(v) => setF({ ...f, pay_type: v })} options={TYPES} />
          </fieldset>
          <Field label={RATE_LABEL[f.pay_type]} prefix="₹" error={errs.rate ?? fieldError(a.error, "rate_paise")}
            hint={f.pay_type === "attendance" ? "Full salary for every working day present; their weekly day off doesn't count against them." : undefined}>
            {(id, desc) => <input className="rl-field__input" id={id} type="number" inputMode="decimal" aria-describedby={desc} value={f.rate} onChange={(e) => { setF({ ...f, rate: e.target.value }); setErrs({ ...errs, rate: "" }); }} />}
          </Field>
          {f.pay_type === "hourly" && (
            <Field label="Hours a day" error={errs.hours ?? fieldError(a.error, "hours_per_day")} hint="Rackline records check-in time only, so each day they check in counts these hours.">
              {(id, desc) => <input className="rl-field__input" id={id} type="number" inputMode="decimal" step="0.5" min={0} max={24} aria-describedby={desc} value={f.hours} onChange={(e) => { setF({ ...f, hours: e.target.value }); setErrs({ ...errs, hours: "" }); }} />}
            </Field>
          )}
          {branches.length > 1 && (
            <Field label="Paid from" hint="The branch whose expenses their salary goes to.">
              {(id) => <select className="rl-field__input" id={id} value={f.branch} onChange={(e) => setF({ ...f, branch: Number(e.target.value) })}>{branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select>}
            </Field>
          )}
          <fieldset className="rl-fieldset"><legend>Every month <span className="rl-optional">(optional)</span></legend>
            {items.map((it, i) => (
              <div className="rl-card rl-card--pad" key={i} style={{ marginBottom: "var(--space-3)" }}>
                <div className="rl-section__head" style={{ marginBottom: "var(--space-2)" }}>
                  <p className="rl-row__title" style={{ margin: 0 }}>{it.kind === "allowance" ? "Allowance" : "Deduction"}</p>
                  <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Remove ${it.label || it.kind}`} onClick={() => setItems(items.filter((_, j) => j !== i))}><Icon as={X} size="sm" /></button>
                </div>
                <div className="rl-pair">
                  <Field label="For">{(id) => <input className="rl-field__input" id={id} maxLength={60} placeholder={it.kind === "allowance" ? "Travel" : "PF"} value={it.label} onChange={(e) => setItem(i, { label: e.target.value })} />}</Field>
                  <Field label="Amount" prefix="₹">{(id) => <input className="rl-field__input" id={id} type="number" inputMode="decimal" value={it.amount} onChange={(e) => setItem(i, { amount: e.target.value })} />}</Field>
                </div>
                <ErrorText>{errs[`item${i}`]}</ErrorText>
              </div>
            ))}
            <div className="rl-pair">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => add("allowance")}><Icon as={Plus} size="sm" />Allowance</button>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => add("deduction")}><Icon as={Minus} size="sm" />Deduction</button>
            </div>
            <p className="rl-field__hint">Added to or taken from every month&apos;s pay. Incentives and referral bonuses go on that month&apos;s payslip.</p>
          </fieldset>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label={editing ? "Save Changes" : "Set Salary"} onClick={save} busy={a.busy} />
      <Sheet open={done} onClose={() => {}} closable={false}>
        <Confirm title={editing ? "Changes saved" : "Salary set"}
          text={`${staff.name}: ${rateText({ pay_type: f.pay_type, rate_paise: toPaise(f.rate), hours_per_day: f.hours || "0" })}${items.length ? `, with ${items.length} monthly ${items.length === 1 ? "line" : "lines"}` : ""}. This month's draft payslip follows it when you update payroll; approved ones don't change.`} />
        <div className="rl-sheet__actions">
          <Link className="rl-button rl-button--block" href={`/staff/${staff.id}`}>Done</Link>
          <Link className="rl-button rl-button--secondary rl-button--block" href="/payroll">Go to Payroll</Link>
        </div>
      </Sheet>
    </div>
  );
}
