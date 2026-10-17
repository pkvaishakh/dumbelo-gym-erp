"use client";
import { Repeat } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useRecurringExpensesList } from "@/api/gen/recurring-expenses/recurring-expenses";
import { PageBar } from "@/components/shell";
import { AddButton, Empty, Icon, Section, Seg, SkeletonRows, Status } from "@/components/ui";
import { day, FREQUENCY, plural, rupees } from "@/lib/format";
import { useSession } from "@/lib/session";

export default function RecurringExpenses() {
  const { branch, branchName } = useSession();
  const [show, setShow] = useState<"true" | "false">("true");
  // A gym has a handful of these: one page of 100 holds them all.
  const q = useRecurringExpensesList({ active: show === "true", limit: 100, ...(branch ? { branch } : {}) });
  const rows = q.data?.data.results ?? [];
  return (
    <div className="rl-app rl-root">
      <PageBar title="Recurring expenses" sub={branchName} back="/expenses" action={<AddButton href="/expenses/recurring/new" label="Add Recurring Expense" />} />
      <main className="rl-app__main">
        <Section label="Show">
          <Seg label="Show" value={show} onChange={setShow} options={[{ value: "true", label: "Running" }, { value: "false", label: "Stopped" }]} />
        </Section>
        <section className="rl-section" aria-label="Recurring expenses">
          <div className="rl-listmeta"><p role="status">{q.isLoading ? "Loading…" : plural(q.data?.data.count ?? 0, "recurring expense")}</p></div>
          {q.isLoading ? <SkeletonRows /> : rows.length ? (
            <ul className="rl-card rl-activity">
              {rows.map((r) => (
                <li key={r.id}><Link className="rl-activity__row" href={`/expenses/recurring/${r.id}`}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Repeat} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{r.name}</span>
                    <span className="rl-row__meta">{FREQUENCY[r.frequency]} • {r.branch_name}{r.is_active && r.next_due ? ` • Next ${day(r.next_due)}` : ""}</span>
                  </span>
                  <span className="rl-activity__amount">{rupees(r.amount_paise)}</span>
                  {!r.is_active && <Status status="off" />}
                </Link></li>
              ))}
            </ul>
          ) : show === "true" ? (
            <Empty icon={Repeat} title="No recurring expenses yet" text="Add rent, electricity and subscriptions once, and each date shows in Dues before it's due.">
              <Link className="rl-button rl-button--block" href="/expenses/recurring/new">Add Recurring Expense</Link>
            </Empty>
          ) : <Empty icon={Repeat} title="Nothing stopped" text="Recurring expenses you stop show here, with their dates." />}
        </section>
      </main>
    </div>
  );
}
