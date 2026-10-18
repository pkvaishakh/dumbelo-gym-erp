"use client";
import { Printer } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { useAccountsRetrieve, useAccountsStatementRetrieve } from "@/api/gen/accounts/accounts";
import { DetailBar } from "@/components/shell";
import { Icon, SkeletonRows } from "@/components/ui";
import { accountMeta } from "@/features/money";
import { day, dayShort, monthLabel, rupees } from "@/lib/format";
import { useSession } from "@/lib/session";

const signed = (p: number) => `${p > 0 ? "+" : "−"}${rupees(Math.abs(p))}`;

/** An account's month to print or save as a PDF from the browser, like the salary slip: on plain paper, the app bar,
 *  the button and the tab bar left out (rl-noprint). */
function PrintStatement() {
  const { id } = useParams<{ id: string }>();
  const asked = useSearchParams().get("month");
  const month = asked && /^\d{4}-\d{2}$/.test(asked) ? asked : undefined;
  const { role } = useSession();
  const acct = useAccountsRetrieve(Number(id)).data?.data;
  const s = useAccountsStatementRetrieve(Number(id), month ? { month } : undefined).data?.data;
  const back = `/money/accounts/${id}/statement${month ? `?month=${month}` : ""}`;
  return (
    <div className="rl-app rl-root">
      <div className="rl-noprint"><DetailBar title="Print statement" back={back} /></div>
      <main className="rl-app__main">
        {!s || !acct ? <SkeletonRows n={6} /> : (
          <>
            <section className="rl-section">
              <div className="rl-card rl-card--pad">
                <p className="rl-row__meta" style={{ margin: 0 }}>{role.gym_name}</p>
                <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>{acct.label}, {monthLabel(s.from.slice(0, 7))}</h2>
                <dl className="rl-facts">
                  <dt>Account</dt><dd>{accountMeta(acct)}</dd>
                  <dt>Days</dt><dd>{day(s.from)} to {day(s.to)}</dd>
                  <dt>Came in</dt><dd>{rupees(s.in_paise)}</dd>
                  <dt>Went out</dt><dd>{rupees(s.out_paise)}</dd>
                  {s.reconciled && <><dt>Reconciled</dt><dd>Up to {day(s.reconciled.up_to)} at {rupees(s.reconciled.bank_balance_paise)}</dd></>}
                </dl>
              </div>
            </section>
            <section className="rl-section" aria-label="Entries">
              <div className="rl-card rl-card--pad">
                <h2 className="rl-section__title" style={{ margin: 0 }}>Entries</h2>
                {/* Long entry names wrap; the amounts keep their width. */}
                <dl className="rl-facts" style={{ gridTemplateColumns: "minmax(0, 1fr) auto" }}>
                  <dt>Opening balance, {dayShort(s.from)}</dt><dd>{rupees(s.opening_paise)}</dd>
                  {s.entries.map((e) => (
                    <Line key={`${e.kind}-${e.id}`} label={`${dayShort(e.on)}, ${e.title}: ${e.meta}${e.reconciled ? " (reconciled)" : ""}`}
                      value={signed(e.amount_paise)} after={`Balance ${rupees(e.balance_paise)}`} />
                  ))}
                </dl>
                {!s.entries.length && <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>Nothing moved this month.</p>}
                <p className="rl-total"><span>Closing balance, {dayShort(s.to)}</span><span>{rupees(s.closing_paise)}</span></p>
              </div>
            </section>
            <section className="rl-section rl-noprint">
              <button className="rl-button rl-button--block" type="button" onClick={() => window.print()}><Icon as={Printer} size="sm" />Print Statement</button>
              <p className="rl-field__hint">To save it as a PDF, choose Save as PDF in the print window.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

/** One entry: what it was on the left; the amount and the balance after it on the right, never broken mid-figure. */
function Line({ label, value, after }: { label: string; value: string; after: string }) {
  return <><dt>{label}</dt><dd style={{ whiteSpace: "nowrap" }}>{value}<br /><span className="rl-row__meta">{after}</span></dd></>;
}

export default function Page() { return <Suspense><PrintStatement /></Suspense>; }
