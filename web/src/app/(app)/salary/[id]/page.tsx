"use client";
import { Printer } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { usePayslipsRetrieve } from "@/api/gen/payslips/payslips";
import { DetailBar } from "@/components/shell";
import { Icon, Section, SkeletonRows } from "@/components/ui";
import { PayslipStatus } from "@/features/money-out";
import { Breakdown, SalaryPayments, TakeHome } from "@/features/payroll";
import { monthLabel } from "@/lib/format";

/** One month of a staff member's own salary: read only. The admin's payslip (/payroll/[id]) is where it changes. */
export default function MyPayslip() {
  const { id } = useParams<{ id: string }>();
  const s = usePayslipsRetrieve(Number(id)).data?.data;
  if (!s) return <div className="rl-app rl-root"><DetailBar title="Salary" back="/salary" /><main className="rl-app__main"><SkeletonRows n={5} /></main></div>;
  return (
    <div className="rl-app rl-root">
      <DetailBar title="Salary" back="/salary"
        action={<Link className="rl-iconbtn rl-iconbtn--plain" href={`/salary/${s.id}/slip`} aria-label="Print Salary Slip"><Icon as={Printer} /></Link>} />
      <main className="rl-app__main">
        <div className="rl-identity">
          <div className="rl-identity__text"><h2 className="rl-identity__name">{monthLabel(s.month)}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{s.branch_name}</span><PayslipStatus status={s.status} payment={s.payment_status} /></p></div>
        </div>
        <TakeHome s={s} />
        <Breakdown s={s} />
        {s.status === "draft" && <p className="rl-field__hint">Not approved yet, so the pay can still change as the month goes.</p>}
        <Section title="Payments">
          <SalaryPayments s={s} />
        </Section>
      </main>
    </div>
  );
}
