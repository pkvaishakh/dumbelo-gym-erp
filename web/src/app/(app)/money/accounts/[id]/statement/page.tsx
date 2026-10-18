"use client";
import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine, Check, Download, FileText, Lock, Printer, Receipt, Undo2, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useAccountsRetrieve, useAccountsStatementRetrieve } from "@/api/gen/accounts/accounts";
import type { AccountStatement, StatementEntry } from "@/api/gen/model";
import { DetailBar } from "@/components/shell";
import { Chips, Empty, ErrorText, Field, Icon, Section, Sheet, SkeletonRows, Stat } from "@/components/ui";
import { day, dayShort, monthLabel, recentMonths, rupees, toPaise } from "@/lib/format";
import { download, statementCsv } from "@/lib/csv";
import { useAction } from "@/lib/hooks";

const ENTRY_ICON = { payment: ArrowDownToLine, expense: Receipt, refund: Undo2, move: ArrowRightLeft } as const;

const signed = (p: number) => `${p > 0 ? "+" : "−"}${rupees(Math.abs(p))}`;
const TOUCH = { width: "var(--touch-min)", height: "var(--touch-min)" };

/** One line of the statement: what it was, the signed amount, and the balance after it. A payment opens its member. */
function EntryRow({ e }: { e: StatementEntry }) {
  const body = (
    <>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={ENTRY_ICON[e.kind]} size="sm" /></span>
      <span className="rl-activity__text">
        <span className="rl-row__title">{e.title}</span>
        <span className="rl-row__meta">{dayShort(e.on)} • {e.meta} • Balance {rupees(e.balance_paise)}</span>
      </span>
      <span className="rl-activity__amount">{signed(e.amount_paise)}</span>
    </>
  );
  return <li>{e.member ? <Link className="rl-activity__row" href={`/members/${e.member}`}>{body}</Link> : <div className="rl-activity__row">{body}</div>}</li>;
}

/** A bank account's line, with a tick for "on the bank's statement too" (a volt fill once ticked). A reconciled one
 *  shows a lock instead, which opens Un-reconcile. */
function TickRow({ e, busy, onTick, onLocked }: { e: StatementEntry; busy: boolean; onTick: () => void; onLocked: () => void }) {
  const label = `${e.title}, ${signed(e.amount_paise)} on ${dayShort(e.on)}`;
  return (
    <li><div className="rl-activity__row">
      {e.reconciled ? (
        <button className="rl-chipicon" type="button" aria-haspopup="dialog" aria-label={`${label}: reconciled. Un-reconcile`} onClick={onLocked}
          style={{ ...TOUCH, border: 0, background: "var(--volt)" }}><Icon as={Lock} size="sm" /></button>
      ) : (
        <button className="rl-chipicon" type="button" aria-pressed={e.ticked} aria-label={`${label}: on the bank's statement`} disabled={busy} onClick={onTick}
          style={{ ...TOUCH, border: e.ticked ? 0 : "1px solid var(--field-line)", background: e.ticked ? "var(--volt)" : "var(--ground)" }}>
          {e.ticked && <Icon as={Check} size="sm" />}
        </button>
      )}
      <span className="rl-activity__text">
        <span className="rl-row__title">{e.title}</span>
        <span className="rl-row__meta">{dayShort(e.on)} • {e.meta} • Balance {rupees(e.balance_paise)}</span>
      </span>
      <span className="rl-activity__amount">{signed(e.amount_paise)}</span>
    </div></li>
  );
}

/** Check the ticked entries against the bank's balance at the end of the last day shown, and lock them. */
function Reconcile({ id, s }: { id: number; s: AccountStatement }) {
  const [bank, setBank] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const typed = bank.trim() !== "";
  const said = toPaise(bank) * (bank.trim().startsWith("-") ? -1 : 1); // an overdrawn account's balance is below zero
  const gap = said - s.cleared_paise;
  async function save() {
    if (!typed) return setErr("Enter the balance on the bank's statement");
    try {
      await a.run(`/api/accounts/${id}/reconcile/`, { up_to: s.to, bank_balance_paise: said }, { refresh: ["/api/accounts/"] });
      setBank("");
    } catch { /* shown */ }
  }
  return (
    <Section title="Check against the bank">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <p className="rl-row__meta" style={{ margin: 0 }}>
          Tick each entry that&apos;s on the bank&apos;s statement, this month and before. The balance it was added with and the ticked entries up to {day(s.to)} come to {rupees(s.cleared_paise)}.
        </p>
        <fieldset className="rl-fieldset"><legend>The bank&apos;s balance at the end of {day(s.to)}</legend>
          <label className={`rl-amount${err ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
            <input type="text" inputMode="decimal" aria-label="The bank's balance in rupees" value={bank} onChange={(e) => { setBank(e.target.value); setErr(undefined); a.clearError(); }} />
          </label>
          {err ? <ErrorText>{err}</ErrorText> : a.error ? <ErrorText>{a.error.message}</ErrorText> : (
            <p className="rl-field__hint" style={{ margin: 0 }}>
              {!typed ? "From the bank's statement or app." : gap === 0 ? "It matches your ticked entries."
                : `${rupees(Math.abs(gap))} ${gap > 0 ? "more" : "less"} than your ticked entries: tick what's missing, or add the bank's charges as a withdrawal.`}
            </p>
          )}
        </fieldset>
        <button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Mark Reconciled"}</button>
        <p className="rl-field__hint">Reconciled entries are locked: correcting or voiding one needs an admin to un-reconcile it first.</p>
      </form>
    </Section>
  );
}

/** Unlock one reconciled entry, with the reason, so it can be corrected or voided. */
function UnreconcileSheet({ id, e, onClose }: { id: number; e: StatementEntry; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function save() {
    if (!reason.trim()) return setErr("Say why, so the next person reading this knows");
    try { await a.run(`/api/accounts/${id}/unreconcile/`, { kind: e.kind, id: e.id, reason: reason.trim() }, { refresh: ["/api/accounts/"] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title="Un-reconcile this entry?">
      <form className="rl-form" noValidate onSubmit={(ev) => { ev.preventDefault(); save(); }}>
        <p className="rl-row__meta">{e.title}, {signed(e.amount_paise)} on {day(e.on)}, was matched with the bank&apos;s statement and locked. Un-reconciling lets it be corrected or voided. Your reason is kept with it.</p>
        <Field label="Reason" error={err}>{(fid, desc) => (
          <input className="rl-field__input" id={fid} aria-describedby={desc} maxLength={200} placeholder="The cheque bounced" value={reason}
            onChange={(ev) => { setReason(ev.target.value); setErr(undefined); }} />
        )}</Field>
        <ErrorText>{a.error?.message}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Unlocking…" : "Un-reconcile"}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep It</button>
        </div>
      </form>
    </Sheet>
  );
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
  const isBank = acct?.kind === "bank";
  const ticking = useAction();
  const [locked, setLocked] = useState<StatementEntry | null>(null);
  const tick = (e: StatementEntry) => {
    ticking.run(`/api/accounts/${id}/tick/`, { entries: [{ kind: e.kind, id: e.id }], ticked: !e.ticked }, { refresh: ["/api/accounts/"] }).catch(() => { /* shown */ });
  };
  return (
    <div className="rl-app rl-root">
      <DetailBar title="Statement" back={`/money/accounts/${id}`} />
      <main className="rl-app__main">
        <Section label="Month">
          <Chips name="statement-month" label="Month" value={month} onChange={(v) => router.replace(v === months[0]!.value ? base : `${base}?month=${v}`, { scroll: false })} options={options} />
        </Section>
        {s && acct && (
          <Section label="Export">
            <div className="rl-actions__contact">
              <button className="rl-button rl-button--secondary rl-button--sm" type="button"
                onClick={() => download(`${acct.label} ${month}.csv`.replace(/[^\w .-]/g, ""), statementCsv(acct.label, s))}><Icon as={Download} size="sm" />Download CSV</button>
              <Link className="rl-button rl-button--secondary rl-button--sm" href={`${base}/print?month=${month}`}><Icon as={Printer} size="sm" />Print or PDF</Link>
            </div>
          </Section>
        )}
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
              {isBank && s?.reconciled && (
                <p className="rl-row__meta" style={{ marginTop: 0 }}>Reconciled up to {day(s.reconciled.up_to)} at {rupees(s.reconciled.bank_balance_paise)}, by {s.reconciled.by_name}.</p>
              )}
              {q.isLoading ? <SkeletonRows n={5} /> : s?.entries.length ? (
                <ul className="rl-card rl-activity">{s.entries.map((e) => isBank
                  ? <TickRow key={`${e.kind}-${e.id}`} e={e} busy={ticking.busy} onTick={() => tick(e)} onLocked={() => setLocked(e)} />
                  : <EntryRow key={`${e.kind}-${e.id}`} e={e} />)}</ul>
              ) : (
                <Empty icon={FileText} title="Nothing this month" text="Payments taken in, expenses paid out and money moved show here, oldest first." />
              )}
              <ErrorText>{ticking.error?.message}</ErrorText>
              <p className="rl-field__hint">Check these against the bank&apos;s statement or the cash counted at the desk. Voided payments, refunds and moves are left out.</p>
            </Section>
            {isBank && s && <Reconcile id={Number(id)} s={s} />}
          </>
        )}
      </main>
      {locked && <UnreconcileSheet key={`${locked.kind}-${locked.id}`} id={Number(id)} e={locked} onClose={() => setLocked(null)} />}
    </div>
  );
}

export default function Page() { return <Suspense><Statement /></Suspense>; }
