"use client";
import { Bell, Building2, CalendarClock, CalendarRange, Pencil, Receipt, Repeat, StickyNote, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useExpenseDuesListInfinite } from "@/api/gen/expense-dues/expense-dues";
import type { ExpenseDue } from "@/api/gen/model";
import { useRecurringExpensesRetrieve } from "@/api/gen/recurring-expenses/recurring-expenses";
import { DetailBar } from "@/components/shell";
import { Details, Empty, ErrorText, Icon, LoadMore, Section, Sheet, SkeletonRows, Status } from "@/components/ui";
import { BillStatus, DueSheet } from "@/features/money-out";
import { day, EXPENSE_CATEGORY, FREQUENCY, PAY_METHOD, plural, rupees } from "@/lib/format";
import { paged, pages, useAction } from "@/lib/hooks";

export default function RecurringExpenseRecord() {
  const { id } = useParams<{ id: string }>();
  const q = useRecurringExpensesRetrieve(Number(id));
  const r = q.data?.data;
  const dates = useExpenseDuesListInfinite({ recurring: Number(id), state: "all", limit: 12 }, { query: paged });
  const { rows, count } = pages(dates);
  const [open, setOpen] = useState<ExpenseDue | null>(null);
  const [stopping, setStopping] = useState(false);
  const a = useAction();
  if (!r) return <div className="rl-app rl-root"><DetailBar title="Recurring expense" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  async function stop() {
    try { await a.run(`/api/recurring-expenses/${r!.id}/stop/`, undefined, { refresh: ["/api/recurring-expenses/", "/api/expense-dues/", "/api/reports/"] }); setStopping(false); } catch { /* shown */ }
  }
  return (
    <div className="rl-app rl-root">
      <DetailBar title={r.name} back="/expenses/recurring"
        action={r.is_active ? <Link className="rl-iconbtn rl-iconbtn--plain" href={`/expenses/recurring/${r.id}/edit`} aria-label="Edit"><Icon as={Pencil} /></Link> : undefined} />
      <main className="rl-app__main">
        <section className="rl-section" aria-label="Amount"><div className="rl-pass">
          <div className="rl-pass__top"><span className="rl-pass__plan">{FREQUENCY[r.frequency]}</span>{!r.is_active && <Status status="off" />}</div>
          <p className="rl-figure">{rupees(r.amount_paise)}</p>
          <div className="rl-pass__dates"><span>{r.is_active ? (r.next_due ? `Next due ${day(r.next_due)}` : "Nothing due yet") : "Stopped"}</span><span>{EXPENSE_CATEGORY[r.category]}</span></div>
        </div></section>
        <Section title="Details">
          <Details rows={[
            { icon: CalendarClock, label: "First due", value: day(r.starts) },
            { icon: CalendarRange, label: "Last date", value: r.ends ? day(r.ends) : "Keeps going" },
            { icon: Bell, label: "Shows in Dues", value: r.remind_days ? `${plural(r.remind_days ?? 0, "day")} before` : "On the day" },
            { icon: Building2, label: "Branch", value: r.branch_name },
            { icon: Wallet, label: "Usually paid by", value: PAY_METHOD[r.method] },
            { icon: Receipt, label: "Paid to", value: r.paid_to },
            { icon: StickyNote, label: "Note", value: r.note },
          ]} />
        </Section>
        <section className="rl-section" aria-label="Dates">
          <div className="rl-section__head"><h2 className="rl-section__title">Dates</h2><p className="rl-section__aside">{plural(count, "date")}</p></div>
          {dates.isLoading ? <SkeletonRows n={3} /> : rows.length ? (
            <>
              <ul className="rl-card rl-activity">
                {rows.map((d) => (
                  <li key={d.id}><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={() => setOpen(d)} style={{ width: "100%", background: "none", border: 0, font: "inherit", textAlign: "left" }}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Repeat} size="sm" /></span>
                    <span className="rl-activity__text"><span className="rl-row__title">{day(d.due_on)}</span><span className="rl-row__meta">{d.paid_on ? `Paid ${day(d.paid_on)}` : d.status === "skipped" ? "Won't be paid" : "Not paid yet"}</span></span>
                    <span className="rl-activity__amount">{rupees(d.paid_paise ?? d.amount_paise)}</span>
                    <BillStatus state={d.state} />
                  </button></li>
                ))}
              </ul>
              <LoadMore q={dates} />
            </>
          ) : <Empty icon={CalendarClock} title="No dates yet" text="Dates show here about a month before they're due." />}
        </section>
        {r.is_active && (
          <Section label="Stop">
            <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setStopping(true)}>Stop Recurring Expense</button>
          </Section>
        )}
      </main>
      {open && <DueSheet key={open.id} due={open} record={false} onClose={() => setOpen(null)} />}
      <Sheet open={stopping} onClose={() => setStopping(false)} title={`Stop ${r.name}?`}>
        <p className="rl-row__meta">No more dates from today. Dates still to come are skipped; late ones stay in Dues to pay or skip. What was paid stays in expenses.</p>
        <ErrorText>{a.error?.message}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={stop}>{a.busy ? "Stopping…" : "Stop It"}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setStopping(false)}>Keep It Going</button>
        </div>
      </Sheet>
    </div>
  );
}
