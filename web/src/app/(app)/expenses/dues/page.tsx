"use client";
import { Banknote, CalendarCheck, CalendarClock, Repeat } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useExpenseDuesListInfinite } from "@/api/gen/expense-dues/expense-dues";
import type { ExpenseDue, ExpenseDuesListState } from "@/api/gen/model";
import { usePayslipsList } from "@/api/gen/payslips/payslips";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Icon, LoadMore, Section, SkeletonRows, Stat } from "@/components/ui";
import { BillStatus, DueSheet, PayslipStatus } from "@/features/money-out";
import { day, monthLabel, plural, rupees } from "@/lib/format";
import { paged, pages, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Summary } from "@/lib/types";

const STATES: { value: ExpenseDuesListState; label: string }[] = [
  { value: "open", label: "To pay" }, { value: "upcoming", label: "Coming up" }, { value: "paid", label: "Paid" }, { value: "skipped", label: "Skipped" },
];

function DuesPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { branch, branchName } = useSession();
  const asked = params.get("state");
  const state = (STATES.some((s) => s.value === asked) ? asked : "open") as ExpenseDuesListState;
  const sum = useGet<Summary>("/api/reports/summary/", { branch }).data?.expense_dues;
  const list = useExpenseDuesListInfinite({ state, ...(branch ? { branch } : {}) }, { query: paged });
  const { rows, count } = pages(list);
  const salaries = usePayslipsList({ owed: true, limit: 100, ...(branch ? { branch } : {}) }, { query: { enabled: state === "open" } }); // a gym's staff fit one page
  const owedSlips = salaries.data?.data.results ?? [];
  const [open, setOpen] = useState<ExpenseDue | null>(null);

  return (
    <div className="rl-app rl-root">
      <PageBar title="Dues" sub={branchName} back="/expenses" />
      <main className="rl-app__main">
        <Section label="To pay">
          <Stat icon={CalendarClock} accent value={sum ? rupees(sum.total_paise) : "–"} label="Bills and salaries to pay"
            note={sum ? `${plural(sum.bills, "bill")}${sum.overdue_bills ? ` (${sum.overdue_bills} late)` : ""} • ${plural(sum.salaries, "salary", "salaries")}` : " "} />
        </Section>
        <Section label="Show">
          <Chips name="due-state" label="Show" value={state} onChange={(v) => router.replace(v === "open" ? "/expenses/dues" : `/expenses/dues?state=${v}`, { scroll: false })} options={STATES} />
        </Section>
        {state === "open" && (owedSlips.length > 0 || salaries.isLoading) && (
          <Section title="Salaries" aside={<Link className="rl-link" href="/payroll"><span>Payroll</span></Link>}>
            {salaries.isLoading ? <SkeletonRows n={2} /> : (
              <ul className="rl-card rl-activity">
                {owedSlips.map((s) => (
                  <li key={s.id}><Link className="rl-activity__row" href={`/payroll/${s.id}`}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
                    <span className="rl-activity__text"><span className="rl-row__title">{s.staff_name}</span><span className="rl-row__meta">{monthLabel(s.month)} • {s.branch_name}</span></span>
                    <span className="rl-activity__amount">{rupees(s.owed_paise)}</span>
                    <PayslipStatus status={s.status} payment={s.payment_status} />
                  </Link></li>
                ))}
              </ul>
            )}
          </Section>
        )}
        <section className="rl-section" aria-label="Bills">
          <div className="rl-section__head">
            <h2 className="rl-section__title">Bills</h2>
            <Link className="rl-link" href="/expenses/recurring"><span>Recurring expenses</span></Link>
          </div>
          <div className="rl-listmeta"><p role="status">{list.isLoading ? "Loading…" : plural(count, "bill")}</p><p>{state === "paid" || state === "skipped" ? "Newest first" : "Soonest first"}</p></div>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <>
              <ul className="rl-card rl-activity">
                {rows.map((d) => (
                  <li key={d.id}><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={() => setOpen(d)} style={{ width: "100%", background: "none", border: 0, font: "inherit", textAlign: "left" }}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Repeat} size="sm" /></span>
                    <span className="rl-activity__text"><span className="rl-row__title">{d.name}</span><span className="rl-row__meta">Due {day(d.due_on)} • {d.branch_name}</span></span>
                    <span className="rl-activity__amount">{rupees(d.paid_paise ?? d.amount_paise)}</span>
                    <BillStatus state={d.state} />
                  </button></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={CalendarCheck} title={state === "open" ? "No bills to pay" : state === "upcoming" ? "Nothing coming up" : `No ${state} bills`}
              text={state === "open" ? "Bills show here a few days before they're due." : "Add rent and bills you pay again and again, and they'll show here."}>
              <Link className="rl-button rl-button--secondary rl-button--block" href="/expenses/recurring/new">Add Recurring Expense</Link>
            </Empty>
          )}
        </section>
      </main>
      {open && <DueSheet key={open.id} due={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

export default function Page() {
  return <Suspense><DuesPage /></Suspense>;
}
