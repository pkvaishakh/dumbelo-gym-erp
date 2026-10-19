"use client";
/* WhatsApp messages as a gym's people read them: a message's status badge (the Console's log too), the gym's log
   filters, and one message in full with Retry for an admin. */
import { AlertCircle, CalendarClock, Check, CheckCheck, MessageCircle, RotateCw, Send, UserRound } from "lucide-react";
import { useState } from "react";

import type { Message } from "@/api/gen/model";
import { Confirm, Details, ErrorText, Field, Seg, Sheet } from "@/components/ui";
import { day, dayTime, MESSAGE_STATUS, phone } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { MESSAGE_LABEL, type GymLogFilters } from "@/lib/messages";

export function MessageBadge({ status }: { status: string }) {
  const s = MESSAGE_STATUS[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

const RECIPIENTS = [{ value: "", label: "Anyone" }, { value: "member", label: "Members" }, { value: "staff", label: "Staff" }];

/** Which message, who to and which days. Each change applies at once; the list behind shows what it finds. */
export function GymLogFilterSheet({ open, onClose, f, go, count }: {
  open: boolean; onClose: () => void; f: GymLogFilters; go: (next: Partial<GymLogFilters>) => void; count?: number;
}) {
  const backwards = Boolean(f.from && f.to && f.from > f.to);
  const any = f.kind || f.recipient || f.from || f.to;
  return (
    <Sheet open={open} onClose={onClose} title="Filter messages">
      <Field label="Message">{(id) => (
        <select className="rl-field__input" id={id} value={f.kind} onChange={(e) => go({ kind: e.target.value })}>
          <option value="">Any message</option>
          {Object.entries(MESSAGE_LABEL).map(([kind, label]) => <option key={kind} value={kind}>{label}</option>)}
        </select>
      )}</Field>
      <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Sent to</p>
      <Seg label="Sent to" value={f.recipient} onChange={(v) => go({ recipient: v })} options={RECIPIENTS} />
      <div className="rl-pair">
        <Field label="From" error={backwards ? "Pick a start date on or before the end date" : undefined}>{(id, desc) => (
          <input className="rl-field__input" id={id} type="date" value={f.from} aria-describedby={desc} aria-invalid={backwards} onChange={(e) => go({ from: e.target.value })} />
        )}</Field>
        <Field label="To">{(id) => <input className="rl-field__input" id={id} type="date" value={f.to} onChange={(e) => go({ to: e.target.value })} />}</Field>
      </div>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" onClick={onClose}>{count === undefined ? "Done" : `Show ${count.toLocaleString("en-IN")} message${count === 1 ? "" : "s"}`}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!any} onClick={() => go({ kind: "", recipient: "", from: "", to: "" })}>Reset</button>
      </div>
    </Sheet>
  );
}

/** One message in full: who it went to, its words, and how it went. An admin can send a failed one again, once:
 *  the API refuses one that may have reached them after all. */
export function MessageSheet({ m, onClose, canRetry }: { m: Message | null; onClose: () => void; canRetry: boolean }) {
  const a = useAction();
  const [again, setAgain] = useState<Message | null>(null);
  const close = () => { setAgain(null); a.clearError(); onClose(); };
  async function retry(id: number) {
    try {
      setAgain(await a.run<Message>(`/api/messages/${id}/retry/`, undefined, { refresh: ["/api/messages/"] }) ?? null);
    } catch { /* shown under the button */ }
  }
  if (again) {
    const went = again.status !== "failed";
    return (
      <Sheet open onClose={close} title={again.kind_label}>
        <Confirm blocked={!went} title={went ? "Sent again" : "It failed again"}
          text={went ? `It went to ${phone(again.to)}. It shows Delivered once it reaches their phone.` : again.error || "It didn't go."} />
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
      </Sheet>
    );
  }
  return (
    <Sheet open={m !== null} onClose={close} title={m?.kind_label}>
      {m && (
        <>
          <Details rows={[
            { icon: UserRound, label: "To", value: `${m.to_name}${m.recipient === "staff" ? " (staff)" : ""}, ${phone(m.to)}` },
            { icon: Send, label: "Status", value: <><MessageBadge status={m.status} /> since {dayTime(m.updated_at)}</> },
            { icon: CalendarClock, label: "Written", value: `${dayTime(m.created_at)}, for ${day(m.for_date)}` },
            ...(m.delivered_at ? [{ icon: Check, label: "Delivered", value: dayTime(m.delivered_at) }] : []),
            ...(m.read_at ? [{ icon: CheckCheck, label: "Read", value: dayTime(m.read_at) }] : []),
            ...(m.attempts > 1 ? [{ icon: RotateCw, label: "Tries", value: String(m.attempts) }] : []),
            ...(m.error ? [{ icon: AlertCircle, label: "Why it failed", value: m.error }] : []),
            ...(m.text ? [{ icon: MessageCircle, label: "What it said", value: m.text }] : []),
          ]} />
          {canRetry && m.can_retry && (
            <div className="rl-sheet__actions">
              <p className="rl-row__meta" style={{ margin: 0 }}>It goes once more, with the same words, to their number as it is now.</p>
              <ErrorText>{a.error?.message}</ErrorText>
              <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => retry(m.id)}>{a.busy ? "Sending…" : "Retry"}</button>
            </div>
          )}
        </>
      )}
    </Sheet>
  );
}
