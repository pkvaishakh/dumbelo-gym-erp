"use client";
import { Plus, Receipt } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useExpensesListInfinite } from "@/api/gen/expenses/expenses";
import { PageBar } from "@/components/shell";
import { Empty, Icon, LoadMore, Section, SkeletonRows, Stat } from "@/components/ui";
import { day, plural, rupees } from "@/lib/format";
import { paged, pages, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const CATEGORIES: Record<string, string> = { rent: "Rent", salaries: "Salaries", utilities: "Utilities", equipment: "Equipment", maintenance: "Maintenance", supplies: "Supplies", marketing: "Marketing", other: "Other" };

export default function ExpensesPage() {
  const { branch, branchName } = useSession();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const list = useExpensesListInfinite({ month, ...(branch ? { branch } : {}) }, { query: paged });
  const totals = useGet<{ total_paise: number; by_category: Record<string, number> }>("/api/expenses/totals/", { month, branch });
  const { rows, count } = pages(list);
  const max = Math.max(1, ...Object.values(totals.data?.by_category ?? {}));
  return (
    <div className="rl-app rl-root">
      <PageBar title="Expenses" sub={branchName} back="/more" />
      <main className="rl-app__main">
        <div className="rl-field" style={{ marginTop: "var(--space-2)" }}>
          <label className="rl-field__label" htmlFor="ex-month">Month</label>
          <div className="rl-field__control"><input className="rl-field__input" id="ex-month" type="month" value={month} onChange={(e) => setMonth(e.target.value)} /></div>
        </div>
        <Section label="Total"><Stat icon={Receipt} value={rupees(totals.data?.total_paise ?? 0)} label="Spent this month" note={plural(count, "expense")} /></Section>
        <Section title="By category">
          <ul className="rl-card rl-barlist" style={{ listStyle: "none", margin: 0, padding: "var(--space-3) var(--space-4)" }}>
            {Object.entries(totals.data?.by_category ?? {}).map(([c, v]) => (
              <li key={c} style={{ padding: "var(--space-1) 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>{CATEGORIES[c] ?? c}</span><strong>{rupees(v)}</strong></div>
                <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: v / max, background: "var(--ink)" }} /></span>
              </li>
            ))}
            {!Object.keys(totals.data?.by_category ?? {}).length && <li className="rl-row__meta">Nothing spent yet this month.</li>}
          </ul>
        </Section>
        <Section title="Expenses" aside={<Link className="rl-link" href="/expenses/new"><span>Add Expense</span></Link>}>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((e) => (
                <li key={e.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Receipt} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{CATEGORIES[e.category]}{e.paid_to ? `, ${e.paid_to}` : ""}</span>
                  <span className="rl-row__meta rl-mrow__meta">{e.branch_name} • {e.spent_on ? day(e.spent_on) : ""}{e.note ? ` • ${e.note}` : ""}</span>
                  <span className="rl-mrow__time">{rupees(e.amount_paise)}</span>
                </div></li>
              ))}
            </ul>
            <LoadMore q={list} /></>
          ) : <Empty icon={Receipt} title="No expenses this month" text="Add rent, salaries and bills to see what each branch costs."><Link className="rl-button rl-button--block" href="/expenses/new"><Icon as={Plus} />Add Expense</Link></Empty>}
        </Section>
      </main>
    </div>
  );
}
