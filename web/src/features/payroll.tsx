"use client";
/* Payroll pieces shared by the payslip, the printable slip, the staff profile and a staff member's My Salary. */
import { Banknote, Printer } from "lucide-react";

import type { PayslipDetail, SalaryRule } from "@/api/gen/model";
import { usePayslipsRetrieve } from "@/api/gen/payslips/payslips";
import { DetailBar } from "@/components/shell";
import { Icon, SkeletonRows } from "@/components/ui";
import { day, LINE_KIND, monthLabel, PAY_METHOD, PAY_TYPE, phone, RATE_PER, rupees } from "@/lib/format";

export const STAFF_ROLE: Record<string, string> = { admin: "Admin", receptionist: "Receptionist", trainer: "Trainer" };

/** The month's take-home pay, what's paid and what's still to pay. */
export function TakeHome({ s }: { s: PayslipDetail }) {
  return (
    <section className="rl-section" aria-label="Take-home pay"><div className="rl-pass">
      <div className="rl-pass__top"><span className="rl-pass__plan">Take-home pay</span></div>
      <p className="rl-figure">{rupees(s.net_paise)}</p>
      <div className="rl-pass__dates"><span>{rupees(s.paid_paise)} paid</span><span>{s.owed_paise ? `${rupees(s.owed_paise)} to pay` : "Nothing left to pay"}</span></div>
    </div></section>
  );
}

/** Each payment on the payslip: the day, how and who paid it, and the amount. */
export function SalaryPayments({ s }: { s: PayslipDetail }) {
  if (!s.payments.length) return <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>Nothing paid yet.</p></div>;
  return (
    <ul className="rl-card rl-activity">
      {s.payments.map((p) => (
        <li key={p.id}><div className="rl-activity__row">
          <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
          <span className="rl-activity__text"><span className="rl-row__title">{day(p.paid_on)}</span><span className="rl-row__meta">{PAY_METHOD[p.method]} • By {p.paid_by_name}{p.note ? ` • ${p.note}` : ""}</span></span>
          <span className="rl-activity__amount">{rupees(p.amount_paise)}</span>
        </div></li>
      ))}
    </ul>
  );
}

/** How the pay is worked out, line by line, ending in the take-home pay. The printable slip shows the same. */
export function Breakdown({ s }: { s: PayslipDetail }) {
  const additions = s.lines.filter((l) => l.kind !== "deduction");
  const deductions = s.lines.filter((l) => l.kind === "deduction");
  const days = s.pay_type === "fixed" ? null : s.pay_type === "attendance" ? `${s.days_present} of ${s.working_days}` : String(s.days_present);
  return (
    <section className="rl-section" aria-label="Breakdown"><div className="rl-card rl-card--pad">
      <dl className="rl-facts">
        <dt>Paid</dt><dd>{PAY_TYPE[s.pay_type]}</dd>
        <dt>Rate</dt><dd>{rupees(s.rate_paise)} {RATE_PER[s.pay_type]}{s.pay_type === "hourly" ? `, ${Number(s.hours_per_day)} hours a day` : ""}</dd>
        {days && <><dt>Days present{s.days_set_by_hand ? " (set by hand)" : ""}</dt><dd>{days}</dd></>}
        <dt>Pay</dt><dd>{rupees(s.pay_paise)}</dd>
      </dl>
      {additions.length > 0 && <dl className="rl-facts">{additions.map((l) => <Line key={l.id} label={`${l.label} (${LINE_KIND[l.kind]?.toLowerCase()})`} value={`+${rupees(l.amount_paise)}`} />)}</dl>}
      {deductions.length > 0 && <dl className="rl-facts">{deductions.map((l) => <Line key={l.id} label={l.label} value={`−${rupees(l.amount_paise)}`} />)}</dl>}
      <p className="rl-total"><span>Take-home pay</span><span>{rupees(s.net_paise)}</span></p>
    </div></section>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return <><dt>{label}</dt><dd>{value}</dd></>;
}

/** "₹800 a day", "₹26,000 a month by days present", "₹250 an hour, 6 hours a day". */
export function rateText(r: Pick<SalaryRule, "pay_type" | "rate_paise" | "hours_per_day">) {
  const base = `${rupees(r.rate_paise)} ${RATE_PER[r.pay_type]}`;
  if (r.pay_type === "attendance") return `${base}, by days present`;
  if (r.pay_type === "hourly") return `${base}, ${Number(r.hours_per_day)} hours a day`;
  return base;
}

/** The salary slip to print or save as a PDF from the browser: the same breakdown as the payslip, on plain paper.
 *  The app bar, the button and the tab bar don't print (rl-noprint). Payroll and My Salary both open it. */
export function SalarySlip({ id, back }: { id: number; back: string }) {
  const s = usePayslipsRetrieve(id).data?.data;
  return (
    <div className="rl-app rl-root">
      <div className="rl-noprint"><DetailBar title="Salary slip" back={back} /></div>
      <main className="rl-app__main">
        {!s ? <SkeletonRows n={6} /> : (
          <>
            <section className="rl-section">
              <div className="rl-card rl-card--pad">
                <p className="rl-row__meta" style={{ margin: 0 }}>{s.gym_name}</p>
                <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>Salary slip, {monthLabel(s.month)}</h2>
                <dl className="rl-facts">
                  <dt>Name</dt><dd>{s.staff_name}</dd>
                  <dt>Role</dt><dd>{STAFF_ROLE[s.staff_role] ?? s.staff_role}</dd>
                  <dt>Branch</dt><dd>{s.branch_name}</dd>
                  {s.staff_phone && <><dt>Mobile number</dt><dd>{phone(s.staff_phone)}</dd></>}
                  <dt>Status</dt><dd>{s.status === "approved" ? `Approved${s.approved_at ? ` ${day(s.approved_at.slice(0, 10))}` : ""}${s.approved_by_name ? ` by ${s.approved_by_name}` : ""}` : "Draft, not approved yet"}</dd>
                </dl>
              </div>
            </section>
            <Breakdown s={s} />
            <section className="rl-section" aria-label="Payments">
              <div className="rl-card rl-card--pad">
                <h2 className="rl-section__title" style={{ margin: 0 }}>Paid</h2>
                {s.payments.length ? (
                  <dl className="rl-facts">
                    {s.payments.map((p) => <Line key={p.id} label={`${day(p.paid_on)}, ${PAY_METHOD[p.method]}`} value={rupees(p.amount_paise)} />)}
                  </dl>
                ) : <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>Nothing paid yet.</p>}
                <p className="rl-total"><span>{s.owed_paise ? "Still to pay" : "Paid in full"}</span><span>{rupees(s.owed_paise || s.paid_paise)}</span></p>
              </div>
            </section>
            <section className="rl-section rl-noprint">
              <button className="rl-button rl-button--block" type="button" onClick={() => window.print()}><Icon as={Printer} size="sm" />Print Salary Slip</button>
              <p className="rl-field__hint">To save it as a PDF, choose Save as PDF in the print window.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
