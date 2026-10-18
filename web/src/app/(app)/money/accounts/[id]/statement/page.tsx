"use client";
import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine, FileText, Receipt, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { useAccountsRetrieve, useAccountsStatementRetrieve } from "@/api/gen/accounts/accounts";
import type { StatementEntry } from "@/api/gen/model";
import { DetailBar } from "@/components/shell";
import { Chips, Empty, Icon, Section, SkeletonRows, Stat } from "@/components/ui";
import { day, dayShort, monthLabel, recentMonths, rupees } from "@/lib/format";

const ENTRY_ICON = { payment: ArrowDownToLine, expense: Receipt, move: ArrowRightLeft } as const;

/** One line of the statement: what it was, the signed amount, and the balance after it. A payment opens its member. */
function EntryRow({ e }: { e: StatementEntry }) {
  const body = (
    <>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={ENTRY_ICON[e.kind]} size="sm" /></span>
      <span className="rl-activity__text">
        <span className="rl-row__title">{e.title}</span>
        <span className="rl-row__meta">{dayShort(e.on)} • {e.meta} • Balance {rupees(e.balance_paise)}</span>
      </span>
      <span className="rl-activity__amount">{e.amount_paise > 0 ? "+" : "−"}{rupees(Math.abs(e.amount_paise))}</span>
    </>
  );
  return <li>{e.member ? <Link className="rl-activity__row" href={`/members/${e.member}`}>{body}</Link> : <div className="rl-activity__row">{body}</div>}</li>;
}

function Statement() {
  const { id } = useParams<{ id: string }>();
  const params = useSearchParams();
  const router = useRouter();
  const acct = useAccountsRetrieve(Number(id)).data?.data;
  // Months from the one it was added in, up to this one: nothing moved it before then.
  const months = recentMonths(12).filter((m) => !acct || m.value >= acct.opened_on.slice(0, 7));
  const asked = params.get("month");
  const month = asked && /^\d{4}-\d{2}$/.test(asked) ? asked : months[0]!.value;
  const q = useAccountsStatementRetrieve(Number(id), { month });
  const s = q.data?.data;
  const options = months.some((m) => m.value === month) ? months : [...months, { value: month, label: monthLabel(month) }];
  const base = `/money/accounts/${id}/statement`;
  return (
    <div className="rl-app rl-root">
      <DetailBar title="Statement" back={`/money/accounts/${id}`} />
      <main className="rl-app__main">
        <Section label="Month">
          <Chips name="statement-month" label="Month" value={month} onChange={(v) => router.replace(v === months[0]!.value ? base : `${base}?month=${v}`, { scroll: false })} options={options} />
        </Section>
        {q.isError ? (
          <p className="rl-row__meta">This account&apos;s statement couldn&apos;t be loaded. Check your connection and try again.</p>
        ) : (
          <>
            <Section label="Balances">
              <div className="rl-kpis rl-kpis--pair">
                <Stat icon={Wallet} value={s ? rupees(s.opening_paise) : "–"} label="Opening" note={s ? `Before ${day(s.from)}` : " "} />
                <Stat icon={Wallet} accent value={s ? rupees(s.closing_paise) : "–"} label="Closing" note={s ? `After ${day(s.to)}` : " "} />
              </div>
              <div className="rl-kpis rl-kpis--pair" style={{ marginTop: "var(--space-3)" }}>
                <Stat icon={ArrowDownToLine} value={s ? rupees(s.in_paise) : "–"} label="Came in" />
                <Stat icon={ArrowUpFromLine} value={s ? rupees(s.out_paise) : "–"} label="Went out" />
              </div>
            </Section>
            <Section title={acct ? acct.label : "Entries"}>
              {q.isLoading ? <SkeletonRows n={5} /> : s?.entries.length ? (
                <ul className="rl-card rl-activity">{s.entries.map((e) => <EntryRow key={`${e.kind}-${e.id}`} e={e} />)}</ul>
              ) : (
                <Empty icon={FileText} title="Nothing this month" text="Payments taken in, expenses paid out and money moved show here, oldest first." />
              )}
              <p className="rl-field__hint">Check these against the bank&apos;s statement or the cash counted at the desk. Voided payments and moves are left out.</p>
            </Section>
          </>
        )}
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><Statement /></Suspense>; }
