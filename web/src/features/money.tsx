"use client";
/* Cash and bank: rows and sheets the money screen and an account's record share. */
import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine, Banknote, CalendarDays, Landmark, StickyNote, UserRound, Wallet, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { Account, BranchMoney, MoneyMove } from "@/api/gen/model";
import { Choices, Confirm, ErrorText, Field, Icon, Sheet } from "@/components/ui";
import { day, lastDigits, moveLabel, rupees } from "@/lib/format";
import { useAction } from "@/lib/hooks";

/** Every read a change to accounts or money moves can change. */
export const MONEY = ["/api/accounts/", "/api/money-moves/"];

export const accountIcon = (kind: string) => (kind === "cash" ? Banknote : Landmark);

/** The second line under an account: its bank and number and who uses it, or that it's a branch's cash. */
export function accountMeta(a: Account) {
  if (a.kind === "cash") return "Cash in hand";
  const used = a.branch_names.length ? a.branch_names.join(", ") : "No branch uses it";
  return `${a.bank_name} ${lastDigits(a.account_number)} • ${used}`;
}

const MOVE_ICON = { deposit: ArrowDownToLine, withdrawal: ArrowUpFromLine, transfer: ArrowRightLeft } as const;

/** One money move. Inside an account's record (`account`), the amount is signed: in or out of that account. */
export function MoveRow({ m, account, onOpen }: { m: MoneyMove; account?: number; onOpen: () => void }) {
  const sign = account === undefined ? "" : m.to_account === account ? "+" : "−";
  const path = [m.from_name, m.to_name].filter(Boolean).join(" to ");
  return (
    <li><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={onOpen}>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={MOVE_ICON[m.kind]} size="sm" /></span>
      <span className="rl-activity__text">
        <span className="rl-row__title">{moveLabel(m)}</span>
        <span className="rl-row__meta">{path} • {day(m.moved_on ?? m.created_at)}{m.note ? ` • ${m.note}` : ""}</span>
      </span>
      <span className="rl-activity__amount" style={m.voided ? { textDecoration: "line-through", color: "var(--ink-muted)" } : undefined}>{sign}{rupees(m.amount_paise)}</span>
      {m.voided && <span className="rl-status rl-status--frozen">Voided</span>}
    </button></li>
  );
}

/** A money move's facts, and Void for one that was wrong (it stays, marked, with the reason). */
export function MoveSheet({ m, onClose }: { m: MoneyMove; onClose: () => void }) {
  const [voiding, setVoiding] = useState(false);
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function voidIt() {
    if (!reason.trim()) return setErr("Say why, so the next person reading this knows");
    try { await a.run(`/api/money-moves/${m.id}/void/`, { reason: reason.trim() }, { refresh: MONEY }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title={voiding ? "Void this move?" : moveLabel(m)}>
      {voiding ? (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); voidIt(); }}>
          <p className="rl-row__meta">The {rupees(m.amount_paise)} goes back where it came from. The move stays on the list, marked voided, with your reason.</p>
          <Field label="Reason" error={err}>{(id, desc) => (
            <input className="rl-field__input" id={id} aria-describedby={desc} maxLength={200} placeholder="Typed twice" value={reason}
              onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />
          )}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--danger rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Voiding…" : "Void It"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setVoiding(false)}>Keep It</button>
          </div>
        </form>
      ) : (
        <>
          <p className="rl-figure rl-sheet__figure">{rupees(m.amount_paise)}</p>
          <dl className="rl-details">
            {([
              [ArrowUpFromLine, "From", m.from_name ?? "Outside the gym"], [ArrowDownToLine, "To", m.to_name ?? "Outside the gym"],
              [CalendarDays, "Date", day(m.moved_on ?? m.created_at)], [StickyNote, "Note", m.note || "Not added"], [UserRound, "Recorded by", m.created_by_name],
              ...(m.voided ? [[Wallet, "Voided", m.void_reason] as const] : []),
            ] satisfies (readonly [LucideIcon, string, string])[]).map(([icon, label, value]) => (
              <div className="rl-detail" key={label}><span className="rl-chipicon" aria-hidden="true"><Icon as={icon} size="sm" /></span><dt>{label}</dt><dd>{value}</dd></div>
            ))}
          </dl>
          <p className="rl-field__hint">Not counted as income or spending: it only moves money between the gym&apos;s accounts, or in and out of them.</p>
          {!m.voided && (
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setVoiding(true)}>Void This Move</button>
            </div>
          )}
        </>
      )}
    </Sheet>
  );
}

/** One branch's money: its cash in hand (or Set Up Cash), and the bank account it uses, to change. */
export function BranchMoneySheet({ branch, accounts, onClose }: { branch: BranchMoney; accounts: Account[]; onClose: () => void }) {
  const banks = accounts.filter((x) => x.kind === "bank" && x.is_active);
  const [pick, setPick] = useState<number>(branch.bank?.id ?? 0);
  const [saved, setSaved] = useState(false);
  const a = useAction();
  const picked = banks.find((x) => x.id === pick);
  async function save() {
    try {
      await a.run("/api/accounts/branch/", { branch: branch.id, account: pick || null }, { refresh: MONEY });
      setSaved(true);
    } catch { /* shown */ }
  }
  if (saved) {
    return (
      <Sheet open onClose={onClose} closable={false}>
        <Confirm title="Changes saved" text={picked
          ? `New UPI, card and bank payments at ${branch.name} go into ${picked.label}, and its bank expenses come out of it. Money already recorded stays where it is.`
          : `${branch.name} has no bank account now. Its UPI, card and bank money isn't counted in any balance until you give it one.`} />
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={onClose}>Done</button></div>
      </Sheet>
    );
  }
  return (
    <Sheet open onClose={onClose} title={branch.name}>
      <p className="rl-sheet__label" style={{ marginTop: 0 }}>Cash in hand</p>
      {branch.cash ? (
        <ul className="rl-card rl-activity">
          <li><Link className="rl-activity__row" href={`/money/accounts/${branch.cash.id}`}>
            <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
            <span className="rl-activity__text"><span className="rl-row__title">{branch.cash.name}</span><span className="rl-row__meta">Cash payments in, cash expenses out</span></span>
            <span className="rl-activity__amount">{rupees(branch.cash.balance_paise)}</span>
          </Link></li>
        </ul>
      ) : (
        <>
          <p className="rl-row__meta">Not set up yet, so {branch.name}&apos;s cash isn&apos;t counted. Count the cash at the desk and set it up with that amount.</p>
          <Link className="rl-button rl-button--secondary rl-button--block" href={`/money/accounts/new?kind=cash&branch=${branch.id}`} style={{ marginTop: "var(--space-3)" }}>Set Up Cash</Link>
        </>
      )}
      <p className="rl-sheet__label">Bank account</p>
      {banks.length ? (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Choices name={`bank-${branch.id}`} value={pick} onChange={setPick} options={[
            ...banks.map((x) => {
              const others = x.branch_names.filter((n) => n !== branch.name);
              return { value: x.id, title: x.label, price: rupees(x.balance_paise), meta: `${x.bank_name} ${lastDigits(x.account_number)}${others.length ? ` • Also used by ${others.join(", ")}` : ""}` };
            }),
            { value: 0, title: "No bank account", meta: "UPI, card and bank money here isn't counted" },
          ]} />
          <p className="rl-field__hint">Its UPI, card and bank payments go into this account and its bank expenses come out of it. Changing it moves new money only.</p>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="submit" disabled={a.busy || pick === (branch.bank?.id ?? 0)}>{a.busy ? "Saving…" : "Save Changes"}</button>
          </div>
        </form>
      ) : (
        <>
          <p className="rl-row__meta">You haven&apos;t added a bank account yet.</p>
          <Link className="rl-button rl-button--secondary rl-button--block" href={`/money/accounts/new?branch=${branch.id}`} style={{ marginTop: "var(--space-3)" }}>Add Bank Account</Link>
        </>
      )}
    </Sheet>
  );
}
