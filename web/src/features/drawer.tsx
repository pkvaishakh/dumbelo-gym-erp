"use client";
/* Closing the cash drawer: a count's row and sheet, shared by the money screen and the desk's cash screen. */
import { Banknote, CalendarDays, Calculator, StickyNote, UserRound, Wallet } from "lucide-react";
import { useState } from "react";

import type { DrawerClose } from "@/api/gen/model";
import { Details, ErrorText, Field, Icon, Sheet } from "@/components/ui";
import { MONEY } from "@/features/money";
import { ago, countDifference, day, rupees } from "@/lib/format";
import { useAction } from "@/lib/hooks";

/** Every read a cash count can change. */
export const DRAWER = ["/api/drawer-closes/", "/api/cash/"];

/** One cash count: which drawer and day, and how far it was from what it should hold. */
export function CountRow({ c, onOpen }: { c: DrawerClose; onOpen: () => void }) {
  return (
    <li><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={onOpen}>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={Calculator} size="sm" /></span>
      <span className="rl-activity__text">
        <span className="rl-row__title">{c.branch_name} cash</span>
        <span className="rl-row__meta">{day(c.day)} • Counted {rupees(c.counted_paise)} by {c.counted_by_name}</span>
      </span>
      <span className="rl-activity__amount">{countDifference(c.difference_paise)}</span>
      {c.settled_at && <span className="rl-status rl-status--active">Settled</span>}
    </button></li>
  );
}

/** A count's facts, and for an admin, Settle: the difference goes in or out of the cash as a deposit or withdrawal. */
export function CountSheet({ c, admin, onClose }: { c: DrawerClose; admin: boolean; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const diff = c.difference_paise;
  const open = diff !== 0 && !c.settled_at;
  async function settle() {
    if (!reason.trim()) return setErr("Say what happened, so the next person reading this knows");
    try { await a.run(`/api/drawer-closes/${c.id}/settle/`, { reason: reason.trim() }, { refresh: [...MONEY, ...DRAWER] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open onClose={onClose} title={`${c.branch_name} cash, ${day(c.day)}`}>
      <p className="rl-figure rl-sheet__figure">{countDifference(diff)}</p>
      <Details rows={[
        { icon: Banknote, label: "Counted", value: rupees(c.counted_paise) },
        { icon: Wallet, label: "Should have held", value: rupees(c.expected_paise) },
        { icon: UserRound, label: "Counted by", value: `${c.counted_by_name}, ${ago(c.counted_at)}` },
        { icon: StickyNote, label: "Note", value: c.note || "Not added" },
        ...(c.settled_at ? [{ icon: CalendarDays, label: "Settled", value: `${c.settled_by_name}: ${c.settle_reason}` }] : []),
      ]} />
      {open && admin && (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); settle(); }}>
          <p className="rl-row__meta">
            {diff < 0 ? `A withdrawal of ${rupees(-diff)} from` : `A deposit of ${rupees(diff)} into`} {c.branch_name} cash, dated {day(c.day)},
            so it holds what was counted. It isn&apos;t counted as income or spending.
          </p>
          <Field label="What happened" error={err}>{(id, desc) => (
            <input className="rl-field__input" id={id} aria-describedby={desc} maxLength={200} placeholder={diff < 0 ? "Change given twice" : "Payment not recorded"}
              value={reason} onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />
          )}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Settling…" : `Settle ${rupees(Math.abs(diff))}`}</button>
          </div>
        </form>
      )}
      {open && !admin && <p className="rl-field__hint">An admin settles the difference. Until then you can count again today.</p>}
    </Sheet>
  );
}
