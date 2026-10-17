"use client";
/* Payroll pieces shared by the payslip, the printable slip and the staff profile. */
import type { PayslipDetail, SalaryRule } from "@/api/gen/model";
import { LINE_KIND, PAY_TYPE, RATE_PER, rupees } from "@/lib/format";

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
