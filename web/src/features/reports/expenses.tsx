"use client";
import { Repeat } from "lucide-react";
import Link from "next/link";

import { useReportsExpensesRetrieve } from "@/api/gen/reports/reports";
import type { ExpensesReport as ExpensesData } from "@/api/gen/model";
import { Icon, Section } from "@/components/ui";
import { dayShort, plural, rangeLabel, rupees, trend } from "@/lib/format";
import { expensesRows } from "@/lib/report-rows";

import { BarList, Lead, moneyBars, SeriesChart } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

/** Expenses: by day, category, method and branch, bills paid from Dues, salaries paid, and what is still owed. */
export function ExpensesReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsExpensesRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  if (print) return <ReportPrint r={r} slug="expenses" q={q} rows={expensesRows} />;
  return (
    <ReportScreen r={r} slug="expenses" q={q} rows={expensesRows} empty={{
      when: (d) => !d.totals.spent_paise && !d.owed.bills && !d.owed.salaries,
      title: "Nothing spent in these days", text: "Expenses, bills paid from Dues and salaries paid show here by the day they're paid.",
    }}>
      {(d) => <Sections d={d} today={r.today} />}
    </ReportScreen>
  );
}

function Sections({ d, today }: { d: ExpensesData; today: string }) {
  const range = rangeLabel(d.from, d.to);
  const o = d.owed;
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Lead title="Expenses" value={rupees(d.totals.spent_paise)} label={`Spent, ${range}. Salaries and bills included`}
          change={trend(d.totals.spent_paise, d.before.spent_paise, d.days)} aside={<Link className="rl-link" href="/expenses"><span>View expenses</span></Link>}>
          <SeriesChart series={d.series} label={`Spent, ${range}`} value={(x) => x.spent_paise} text={rupees} money today={today} />
        </Lead>
        {d.by_category.length > 0 && <Section title="By category"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_category)} /></div></Section>}
        {d.by_method.length > 0 && <Section title="By method"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_method)} /></div></Section>}
        {d.by_branch.length > 1 && <Section title="By branch"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_branch)} /></div></Section>}
      </div>
      <div className="rl-app__col">
        <Section title="Still owed now" aside={o.bills || o.salaries ? <Link className="rl-link" href="/expenses/dues"><span>View dues</span></Link> : undefined}>
          <div className="rl-card rl-card--pad">
            <dl className="rl-facts">
              <dt>{o.bills ? plural(o.bills, "bill") : "Bills"}{o.overdue_bills ? `, ${o.overdue_bills} overdue` : ""}</dt><dd>{rupees(o.bills_paise)}</dd>
              <dt>{o.salaries ? plural(o.salaries, "salary", "salaries") : "Salaries"}</dt><dd>{rupees(o.salaries_paise)}</dd>
            </dl>
          </div>
        </Section>
        {d.salaries.people.length > 0 && (
          <Section title="Salaries paid">
            <div className="rl-card rl-card--pad">
              <BarList rows={d.salaries.people.map((p) => ({ key: String(p.id), label: p.name, value: p.paid_paise, text: rupees(p.paid_paise) }))} />
            </div>
          </Section>
        )}
        {d.bills.rows.length > 0 && (
          <Section title="Bills paid from Dues">
            <ul className="rl-card rl-activity">
              {d.bills.rows.map((b) => (
                <li key={b.id}><div className="rl-activity__row">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Repeat} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{b.name}</span>
                    <span className="rl-row__meta">Paid {dayShort(b.paid_on)} • Due {dayShort(b.due_on)}</span>
                  </span>
                  <span className="rl-activity__amount">{rupees(b.amount_paise)}</span>
                </div></li>
              ))}
            </ul>
            {d.bills.count > d.bills.rows.length && <p className="rl-field__hint">The latest {d.bills.rows.length} of {d.bills.count}.</p>}
          </Section>
        )}
      </div>
    </div>
  );
}
