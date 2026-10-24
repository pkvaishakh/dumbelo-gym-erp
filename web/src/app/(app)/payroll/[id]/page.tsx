"use client";
import { Minus, Plus, Printer } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { PayslipDetail, PayslipLine, PayslipLineKindEnum } from "@/api/gen/model";
import { usePayslipsRetrieve } from "@/api/gen/payslips/payslips";
import { DetailBar } from "@/components/shell";
import { Chips, ErrorText, Field, Icon, Photo, Section, Sheet, SkeletonRows } from "@/components/ui";
import { PaySheet, PayslipStatus } from "@/features/money-out";
import { Breakdown, SalaryPayments, STAFF_ROLE, TakeHome } from "@/features/payroll";
import { LINE_KIND, monthLabel, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";

const REFRESH = ["/api/payslips/", "/api/reports/"];

export default function PayslipRecord() {
  const { id } = useParams<{ id: string }>();
  const s = usePayslipsRetrieve(Number(id)).data?.data;
  const [sheet, setSheet] = useState<"days" | "line" | "pay" | "reopen" | null>(null);
  const [removing, setRemoving] = useState<PayslipLine | null>(null);
  const a = useAction();
  if (!s) return <div className="rl-app rl-root"><DetailBar title="Payslip" back="/payroll" /><main className="rl-app__main"><SkeletonRows n={5} /></main></div>;
  const draft = s.status === "draft";
  const payable = s.owed_paise > 0 && (!draft || s.pay_type === "daily"); // the API's rule: approve first, except daily wages
  const act = async (path: string) => { try { await a.run(`/api/payslips/${s.id}/${path}/`, undefined, { refresh: REFRESH }); setSheet(null); } catch { /* shown */ } };
  const month = s.month.slice(0, 7);
  return (
    <div className="rl-app rl-root">
      <DetailBar title="Payslip" back={`/payroll?month=${month}`}
        action={<Link className="rl-iconbtn rl-iconbtn--plain" href={`/payroll/${s.id}/slip`} aria-label="Print Salary Slip"><Icon as={Printer} /></Link>} />
      <main className="rl-app__main">
        <div className="rl-identity">
          <Photo name={s.staff_name} size="xl" />
          <div className="rl-identity__text"><h2 className="rl-identity__name">{s.staff_name}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{STAFF_ROLE[s.staff_role] ?? s.staff_role} • {monthLabel(s.month)}</span><PayslipStatus status={s.status} payment={s.payment_status} /></p></div>
        </div>
        <TakeHome s={s} />
        <Breakdown s={s} />
        {draft && (
          <Section title="This month">
            <ul className="rl-card rl-activity">
              {s.lines.map((l) => (
                <li key={l.id}><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={() => setRemoving(l)} style={{ width: "100%", background: "none", border: 0, font: "inherit", textAlign: "left" }}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={l.kind === "deduction" ? Minus : Plus} size="sm" /></span>
                  <span className="rl-activity__text"><span className="rl-row__title">{l.label}</span><span className="rl-row__meta">{LINE_KIND[l.kind]}{l.from_rule ? " • Every month" : " • This month only"}</span></span>
                  <span className="rl-activity__amount">{l.kind === "deduction" ? "−" : "+"}{rupees(l.amount_paise)}</span>
                </button></li>
              ))}
              {!s.lines.length && <li style={{ padding: "var(--space-4)" }}><p className="rl-row__meta" style={{ margin: 0 }}>No allowances, incentives or deductions yet.</p></li>}
            </ul>
            <div className="rl-sheet__actions" style={{ marginTop: "var(--space-3)" }}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSheet("line")}>Add Incentive, Bonus or Deduction</button>
              {s.pay_type !== "fixed" && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSheet("days")}>Change Days Present</button>}
            </div>
          </Section>
        )}
        <Section label="Actions">
          <div className="rl-sheet__actions" style={{ marginTop: 0 }}>
            {draft && <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => act("approve")}>{a.busy ? "Approving…" : `Approve ${rupees(s.net_paise)}`}</button>}
            {payable && <button className={`rl-button rl-button--block${draft ? " rl-button--secondary" : ""}`} type="button" onClick={() => setSheet("pay")}>Pay {s.paid_paise ? "More" : "Salary"}</button>}
            {!draft && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setSheet("reopen")}>Reopen to Change</button>}
          </div>
          {!sheet && <ErrorText>{a.error?.message}</ErrorText>}
          {draft && s.pay_type !== "daily" && <p className="rl-field__hint">Approve the salary to pay it. A draft keeps following check-ins until then.</p>}
        </Section>
        <Section title="Payments">
          <SalaryPayments s={s} />
          <p className="rl-listmore"><Link className="rl-link" href={`/staff/${s.staff}`}><span>{s.staff_name}&apos;s salary and history</span></Link></p>
        </Section>
      </main>
      {sheet === "days" && <DaysSheet s={s} onClose={() => setSheet(null)} />}
      {sheet === "line" && <LineSheet s={s} onClose={() => setSheet(null)} />}
      {sheet === "pay" && <PaySheet open part onClose={() => setSheet(null)} title={`Pay ${s.staff_name}`} owed={s.owed_paise} method="bank" url={`/api/payslips/${s.id}/pay/`}
        done={(p) => `${s.staff_name}, ${monthLabel(s.month)}.${s.owed_paise - p > 0 ? ` ${rupees(s.owed_paise - p)} is still to pay.` : " Paid in full."} It's added to expenses under Salaries.`} />}
      <Sheet open={sheet === "reopen"} onClose={() => setSheet(null)} title="Reopen this salary?">
        <p className="rl-row__meta">It goes back to a draft so you can change it, and follows check-ins again. What&apos;s paid stays, and the pay can&apos;t drop below it.</p>
        <ErrorText>{a.error?.message}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={() => act("reopen")}>Reopen</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSheet(null)}>Keep Approved</button>
        </div>
      </Sheet>
      {removing && <RemoveLineSheet s={s} line={removing} onClose={() => setRemoving(null)} />}
    </div>
  );
}

function DaysSheet({ s, onClose }: { s: PayslipDetail; onClose: () => void }) {
  const [n, setN] = useState(String(s.days_present));
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function save() {
    const v = Number(n);
    if (!Number.isInteger(v) || v < 0 || v > 31) return setErr("Enter a whole number of days, 0 to 31");
    try { await a.run(`/api/payslips/${s.id}/days/`, { days_present: v }, { refresh: REFRESH }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title="Days present">
      <p className="rl-row__meta">{s.staff_name} checked in on the days counted here. Change it for a day they worked without checking in, or a paid leave.</p>
      <Field label="Days present" error={err} hint={s.pay_type === "attendance" ? `${s.working_days} working days in ${monthLabel(s.month)}` : undefined}>
        {(id, desc) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={0} max={31} aria-describedby={desc} value={n} onChange={(e) => { setN(e.target.value); setErr(undefined); }} />}
      </Field>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Days"}</button></div>
    </Sheet>
  );
}

const KINDS = Object.entries(LINE_KIND).map(([value, label]) => ({ value: value as PayslipLineKindEnum, label }));

function LineSheet({ s, onClose }: { s: PayslipDetail; onClose: () => void }) {
  const [f, setF] = useState({ kind: "incentive" as PayslipLineKindEnum, label: "", amount: "" });
  const [errs, setErrs] = useState<{ label?: string; amount?: string }>({});
  const a = useAction();
  async function save() {
    const e = { label: f.label.trim() ? undefined : "Say what it's for, like PT sessions or Advance", amount: toPaise(f.amount) > 0 ? undefined : "Enter the amount" };
    setErrs(e);
    if (e.label || e.amount) return;
    try { await a.run(`/api/payslips/${s.id}/lines/`, { kind: f.kind, label: f.label.trim(), amount_paise: toPaise(f.amount) }, { refresh: REFRESH }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title={`Add to ${monthLabel(s.month)}`}>
      <Chips name="line-kind" label="What it is" scroll={false} value={f.kind} onChange={(v) => setF({ ...f, kind: v })} options={KINDS} />
      <Field label="For" error={errs.label}>{(id, desc) => <input className="rl-field__input" id={id} maxLength={60} aria-describedby={desc} placeholder={f.kind === "deduction" ? "Advance" : f.kind === "referral" ? "2 members joined" : "PT sessions"} value={f.label} onChange={(e) => setF({ ...f, label: e.target.value })} />}</Field>
      <Field label="Amount" prefix="₹" error={errs.amount}>{(id, desc) => <input className="rl-field__input" id={id} type="number" inputMode="decimal" aria-describedby={desc} value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} />}</Field>
      <p className="rl-field__hint">For this month only. Allowances and deductions paid every month go on their salary.</p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Adding…" : `Add ${LINE_KIND[f.kind]}`}</button></div>
    </Sheet>
  );
}

function RemoveLineSheet({ s, line, onClose }: { s: PayslipDetail; line: PayslipLine; onClose: () => void }) {
  const a = useAction();
  async function remove() {
    try { await a.run(`/api/payslips/${s.id}/remove-line/`, { line: line.id }, { refresh: REFRESH }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title={`Remove ${line.label}?`}>
      <p className="rl-row__meta">{LINE_KIND[line.kind]} of {rupees(line.amount_paise)}, from {monthLabel(s.month)} only.{line.from_rule ? " It comes from their salary, so it comes back when payroll is updated unless you change the salary." : ""}</p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={remove}>Remove</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep It</button>
      </div>
    </Sheet>
  );
}
