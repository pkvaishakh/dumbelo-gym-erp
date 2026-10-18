"use client";
import { ArrowRightLeft, Banknote, Landmark, Wallet } from "lucide-react";
import Link from "next/link";

import { useReportsMoneyRetrieve } from "@/api/gen/reports/reports";
import type { MoneyReport as MoneyData, ReportMove } from "@/api/gen/model";
import { Icon, Section, Stat } from "@/components/ui";
import { countDifference, dayShort, plural, rupees } from "@/lib/format";
import { moneyRows } from "@/lib/report-rows";
import { changeSince } from "@/lib/reports";

import { TrendText } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

/** Cash and bank: each account's balance before and after the days, in and out, money moves, cash counts and the
 *  latest reconciliation. A bank account branches share is shown whole, once. */
export function MoneyReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsMoneyRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  if (print) return <ReportPrint r={r} slug="money" q={q} rows={moneyRows} />;
  return (
    <ReportScreen r={r} slug="money" q={q} rows={moneyRows} empty={{
      when: (d) => !d.accounts.length,
      title: r.branch === null ? "No cash or bank accounts yet" : "This branch has no accounts yet",
      text: "Set up each branch's cash in hand and the bank accounts it uses, and their money shows here.",
      action: <Link className="rl-button rl-button--secondary" href="/money">Open Cash and Bank</Link>,
    }}>
      {(d) => <Sections d={d} />}
    </ReportScreen>
  );
}

const moveTitle = (m: ReportMove) => (m.kind === "deposit" ? "Deposit" : m.kind === "withdrawal" ? "Withdrawal" : `${m.from_name} to ${m.to_name}`);

function Sections({ d }: { d: MoneyData }) {
  const t = d.totals;
  const c = d.counts;
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Section title="Total funds">
          <div className="rl-kpis rl-kpis--pair">
            <Stat icon={Wallet} value={rupees(t.opening_paise)} label="Opening" note={`Before ${dayShort(d.from)}`} />
            <Stat icon={Wallet} accent value={rupees(t.closing_paise)} label="Closing" note={<TrendText t={changeSince(t.closing_paise, t.opening_paise, d.from)} />} />
          </div>
          <div className="rl-card rl-card--pad" style={{ marginTop: "var(--space-3)" }}>
            <dl className="rl-facts">
              <dt>Cash in hand</dt><dd>{rupees(t.cash_closing_paise)}</dd>
              <dt>Bank</dt><dd>{rupees(t.bank_closing_paise)}</dd>
            </dl>
            <p className="rl-field__hint" style={{ marginBottom: 0 }}>On {dayShort(d.to)}. Each account counted once, however many branches use it.</p>
          </div>
        </Section>
        <Section title="Accounts" aside={<Link className="rl-link" href="/money"><span>Cash and bank</span></Link>}>
          <ul className="rl-card rl-activity">
            {d.accounts.map((a) => (
              <li key={a.id}><Link className="rl-activity__row" href={`/money/accounts/${a.id}`}>
                <span className="rl-chipicon" aria-hidden="true"><Icon as={a.kind === "cash" ? Banknote : Landmark} size="sm" /></span>
                <span className="rl-activity__text">
                  <span className="rl-row__title">{a.name}{a.is_active ? "" : " (deactivated)"}</span>
                  <span className="rl-row__meta">
                    Opening {rupees(a.opening_paise)} • In {rupees(a.in_paise)} • Out {rupees(a.out_paise)}
                    {a.shared_with.length > 0 && ` • Shared with ${a.shared_with.join(", ")}`}
                    {a.reconciled && ` • Reconciled to ${dayShort(a.reconciled.up_to)}`}
                  </span>
                </span>
                <span className="rl-activity__amount">{rupees(a.closing_paise)}</span>
              </Link></li>
            ))}
          </ul>
          <p className="rl-field__hint">The amount on the right is each account&apos;s balance after {dayShort(d.to)}.</p>
        </Section>
      </div>
      <div className="rl-app__col">
        <Section title="Cash counts">
          <div className="rl-card rl-card--pad">
            <dl className="rl-facts">
              <dt>Counts at close</dt><dd>{c.count}</dd>
              <dt>Short, in all</dt><dd>{rupees(c.short_paise)}</dd>
              <dt>Over, in all</dt><dd>{rupees(c.over_paise)}</dd>
              <dt>Waiting for an admin to settle</dt><dd style={c.to_settle ? { color: "var(--attention)" } : undefined}>{c.to_settle}</dd>
            </dl>
          </div>
          {c.rows.length > 0 && (
            <ul className="rl-card rl-activity" style={{ marginTop: "var(--space-3)" }}>
              {c.rows.map((x) => (
                <li key={x.id}><div className="rl-activity__row">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{x.branch_name}</span>
                    <span className="rl-row__meta">{dayShort(x.day)} • Counted {rupees(x.counted_paise)}{x.difference_paise ? (x.settled ? " • Settled" : " • Not settled") : ""}</span>
                  </span>
                  <span className="rl-activity__amount">{countDifference(x.difference_paise)}</span>
                </div></li>
              ))}
            </ul>
          )}
          {c.count > c.rows.length && <p className="rl-field__hint">The latest {c.rows.length} of {c.count}.</p>}
        </Section>
        <Section title="Money moves">
          {d.moves.rows.length ? (
            <ul className="rl-card rl-activity">
              {d.moves.rows.map((m) => (
                <li key={m.id}><div className="rl-activity__row">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={ArrowRightLeft} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{moveTitle(m)}</span>
                    <span className="rl-row__meta">{dayShort(m.on)}{m.kind !== "transfer" && ` • ${m.to_name ?? m.from_name}`}{m.note && ` • ${m.note}`}</span>
                  </span>
                  <span className="rl-activity__amount">{rupees(m.amount_paise)}</span>
                </div></li>
              ))}
            </ul>
          ) : <p className="rl-row__meta" style={{ margin: 0 }}>No money moved between accounts in these days.</p>}
          {d.moves.count > d.moves.rows.length && <p className="rl-field__hint">The latest {d.moves.rows.length} of {plural(d.moves.count, "move")}.</p>}
          <p className="rl-field__hint">Money moves are never income or spending, so Revenue and Expenses leave them out.</p>
        </Section>
      </div>
    </div>
  );
}
