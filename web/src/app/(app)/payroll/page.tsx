"use client";
import { format, subMonths } from "date-fns";
import { Banknote, Calculator, CircleCheck, UserRoundX, Wallet } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { usePayslipsList, usePayslipsSummaryRetrieve } from "@/api/gen/payslips/payslips";
import { PageBar } from "@/components/shell";
import { Chips, Empty, ErrorText, Photo, Section, SkeletonRows, Stat } from "@/components/ui";
import { PayslipStatus } from "@/features/money-out";
import { monthLabel, PAY_TYPE_SHORT, plural, rupees } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

/** This month and the five before it, newest first: payroll is worked out for months gone by, not ahead. */
function recentMonths(now = new Date()) {
  return Array.from({ length: 6 }, (_, i) => {
    const m = subMonths(now, i);
    return { value: format(m, "yyyy-MM"), label: i === 0 ? "This month" : format(m, "MMM yyyy") };
  });
}

function PayrollPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { branch, branchName } = useSession();
  const months = recentMonths();
  const asked = params.get("month");
  const month = asked && /^\d{4}-\d{2}$/.test(asked) ? asked : months[0]!.value;
  const sum = usePayslipsSummaryRetrieve({ month, ...(branch ? { branch } : {}) }).data?.data;
  const list = usePayslipsList({ month, limit: 100, ...(branch ? { branch } : {}) }); // one row per staff member: one page holds a gym's staff
  const rows = list.data?.data.results ?? [];
  const a = useAction();
  const options = months.some((m) => m.value === month) ? months : [...months, { value: month, label: monthLabel(month) }];

  async function workOut() {
    try { await a.run("/api/payslips/generate/", { month }, { refresh: ["/api/payslips/", "/api/reports/"] }); } catch { /* shown */ }
  }
  const toPay = sum ? sum.net_paise - sum.paid_paise : 0;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Payroll" sub={branchName} back="/expenses" />
      <main className="rl-app__main">
        <Section label="Month">
          <Chips name="pay-month" label="Month" value={month} onChange={(v) => router.replace(v === months[0]!.value ? "/payroll" : `/payroll?month=${v}`, { scroll: false })} options={options} />
        </Section>
        <Section label="Totals">
          <div className="rl-kpis rl-kpis--pair">
            <Stat icon={Wallet} accent value={sum ? rupees(toPay) : "–"} label="Still to pay" note={sum ? `Of ${rupees(sum.net_paise)} for ${monthLabel(month)}` : " "} />
            <Stat icon={CircleCheck} value={sum ? `${sum.approved} of ${sum.payslips}` : "–"} label="Approved" note={sum ? `${rupees(sum.paid_paise)} paid` : " "} />
          </div>
        </Section>
        <Section label="Work out">
          <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={workOut}>
            {a.busy ? "Working out…" : sum?.payslips ? "Update Payroll" : "Work Out Payroll"}
          </button>
          <ErrorText>{a.error?.message}</ErrorText>
          <p className="rl-field__hint">Pay comes from each salary and the days they checked in. Drafts update every time; approved salaries stay as approved.</p>
        </Section>
        {!!sum?.staff_without_salary && (
          <Section label="Missing salaries">
            <ul className="rl-attn"><li><Link className="rl-attn__row" href="/staff">
              <span className="rl-attn__count">{sum.staff_without_salary}</span>
              <span className="rl-attn__text"><span className="rl-row__title">{plural(sum.staff_without_salary, "person", "people")} with no salary set</span><span className="rl-row__meta">Set it on their profile to include them</span></span>
            </Link></li></ul>
          </Section>
        )}
        <section className="rl-section" aria-label="Payslips">
          <div className="rl-section__head"><h2 className="rl-section__title">{monthLabel(month)}</h2><p className="rl-section__aside">{plural(rows.length, "payslip")}</p></div>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((s) => (
                <li key={s.id}><Link className="rl-mrow" href={`/payroll/${s.id}`}>
                  <Photo name={s.staff_name} />
                  <span className="rl-row__title rl-mrow__name">{s.staff_name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{rupees(s.net_paise)} • {PAY_TYPE_SHORT[s.pay_type]}{s.pay_type !== "fixed" ? ` • ${plural(s.days_present, "day")}` : ""}</span>
                  <PayslipStatus status={s.status} payment={s.payment_status} />
                </Link></li>
              ))}
            </ul>
          ) : (
            <Empty icon={sum?.staff_without_salary ? UserRoundX : Calculator} title={`No payslips for ${monthLabel(month)}`}
              text={sum?.staff_without_salary && !sum.payslips ? "Set your staff's salaries first, then work out payroll." : "Work out payroll to make a payslip for each person with a salary."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={workOut}><Banknote className="rl-icon rl-icon--sm" strokeWidth={1.75} aria-hidden />Work Out Payroll</button>
            </Empty>
          )}
        </section>
      </main>
    </div>
  );
}

export default function Page() {
  return <Suspense><PayrollPage /></Suspense>;
}
