"use client";
import { Banknote } from "lucide-react";
import Link from "next/link";

import { usePayslipsListInfinite } from "@/api/gen/payslips/payslips";
import { PageBar } from "@/components/shell";
import { Empty, Icon, LoadMore, SkeletonRows } from "@/components/ui";
import { PayslipStatus } from "@/features/money-out";
import { monthLabel, plural, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** A receptionist's or trainer's own salary, month by month, once the gym has approved it (the API sends no one else's). */
export default function MySalary() {
  const q = usePayslipsListInfinite(undefined, { query: paged });
  const { rows, count } = pages(q);
  return (
    <div className="rl-app rl-root">
      <PageBar title="My Salary" sub={q.isLoading ? "" : plural(count, "month")} back="/more" />
      <main className="rl-app__main">
        <section className="rl-section">
          {q.isLoading ? <SkeletonRows /> : rows.length ? (
            <>
              <ul className="rl-card rl-activity">
                {rows.map((p) => (
                  <li key={p.id}><Link className="rl-activity__row" href={`/salary/${p.id}`}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
                    <span className="rl-activity__text"><span className="rl-row__title">{monthLabel(p.month)}</span><span className="rl-row__meta">{rupees(p.paid_paise)} paid of {rupees(p.net_paise)}</span></span>
                    <PayslipStatus status={p.status} payment={p.payment_status} />
                  </Link></li>
                ))}
              </ul>
              <LoadMore q={q} />
              <p className="rl-field__hint">A month shows here once the gym approves your salary for it.</p>
            </>
          ) : <Empty icon={Banknote} title="No salary yet" text="Once the gym approves your salary for a month, it shows up here with what's been paid." />}
        </section>
      </main>
    </div>
  );
}
