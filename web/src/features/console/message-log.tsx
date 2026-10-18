"use client";
/* The Console's WhatsApp log: its filters (in the address), the filter sheet, and one message's sheet. */
import { AlertCircle, Building2, CalendarClock, Check, CheckCheck, FileText, Hash, IndianRupee, MessageCircle, RotateCw, Send, UserRound, X } from "lucide-react";
import { useState } from "react";

import type { ConsoleMessage } from "@/api/gen/model";
import { usePlatformGymsList, usePlatformWhatsappAccountsList, usePlatformWhatsappTemplatesList } from "@/api/gen/platform/platform";
import { Details, Field, Icon, SearchField, Sheet } from "@/components/ui";
import { day, dayTime, lastDigits, MESSAGE_STATUS, rupees } from "@/lib/format";
import { useSearch } from "@/lib/hooks";

export type LogFilters = { status: string; gym: string; account: string; template: string; from: string; to: string };
export const NO_FILTERS: LogFilters = { status: "all", gym: "", account: "", template: "", from: "", to: "" };

/** Filters live in the address, so Back and a shared link keep the log as it was. */
export function logUrl(f: LogFilters) {
  const p = new URLSearchParams(Object.entries(f).filter(([k, v]) => v && !(k === "status" && v === "all")));
  return `/console/messages${p.size ? `?${p}` : ""}`;
}

export function MessageBadge({ status }: { status: string }) {
  const s = MESSAGE_STATUS[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

const accountLabel = (a: { display_number: string; is_shared: boolean; gym_name?: string | null }) => `${a.display_number} • ${a.is_shared ? "Shared" : a.gym_name ?? "A gym's own"}`;

/** Gym, number, template and days. Each change applies at once; the list behind shows what it finds. */
export function LogFilterSheet({ open, onClose, f, go, gymName, count }: {
  open: boolean; onClose: () => void; f: LogFilters; go: (next: Partial<LogFilters>) => void; gymName?: string; count?: number;
}) {
  const [text, setText] = useState("");
  const q = useSearch(text);
  const gyms = usePlatformGymsList({ q, limit: 5 }, { query: { enabled: open && !f.gym && q.length >= 2 } });
  const accounts = usePlatformWhatsappAccountsList({ limit: 100 }, { query: { enabled: open } });
  const templates = usePlatformWhatsappTemplatesList({ limit: 100, ...(f.account ? { account: Number(f.account) } : {}) }, { query: { enabled: open } });
  const backwards = Boolean(f.from && f.to && f.from > f.to);
  const any = f.gym || f.account || f.template || f.from || f.to;
  return (
    <Sheet open={open} onClose={onClose} title="Filter messages">
      <p className="rl-sheet__label" style={{ marginTop: 0, marginBottom: "var(--space-2)" }}>Gym</p>
      {f.gym ? (
        <ul className="rl-sheet__list" style={{ marginTop: 0 }}>
          <li><button className="rl-sheet__item" type="button" aria-label={`${gymName ?? "This gym"}: tap for any gym`} onClick={() => go({ gym: "" })}>
            <span className="rl-chipicon"><Icon as={Building2} size="sm" /></span><span className="rl-sheet__text">{gymName ?? "This gym"}</span>
            <Icon as={X} size="sm" />
          </button></li>
        </ul>
      ) : (
        <>
          <SearchField value={text} onChange={setText} placeholder="Gym name or short name" label="Find a gym" />
          {q.length >= 2 && (
            <ul className="rl-sheet__list">
              {(gyms.data?.data.results ?? []).map((g) => (
                <li key={g.id}><button className="rl-sheet__item" type="button" onClick={() => { setText(""); go({ gym: String(g.id) }); }}>
                  <span className="rl-chipicon"><Icon as={Building2} size="sm" /></span><span className="rl-sheet__text">{g.name}</span>
                </button></li>
              ))}
              {gyms.data && !gyms.data.data.results.length && <li className="rl-row__meta">No gym matches “{q}”.</li>}
            </ul>
          )}
        </>
      )}
      <Field label="WhatsApp number">{(id) => (
        <select className="rl-field__input" id={id} value={f.account} onChange={(e) => go({ account: e.target.value, template: "" })}>
          <option value="">Any number</option>
          {(accounts.data?.data.results ?? []).map((a) => <option key={a.id} value={a.id}>{accountLabel(a)}</option>)}
        </select>
      )}</Field>
      <Field label="Template">{(id) => (
        <select className="rl-field__input" id={id} value={f.template} onChange={(e) => go({ template: e.target.value })}>
          <option value="">Any template</option>
          {(templates.data?.data.results ?? []).map((t) => <option key={t.id} value={t.id}>{t.kind_label} • {t.name} ({t.language})</option>)}
        </select>
      )}</Field>
      <div className="rl-pair">
        <Field label="Sent from" error={backwards ? "Pick a start date on or before the end date" : undefined}>{(id, desc) => (
          <input className="rl-field__input" id={id} type="date" value={f.from} aria-describedby={desc} aria-invalid={backwards} onChange={(e) => go({ from: e.target.value })} />
        )}</Field>
        <Field label="To">{(id) => <input className="rl-field__input" id={id} type="date" value={f.to} onChange={(e) => go({ to: e.target.value })} />}</Field>
      </div>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" onClick={onClose}>{count === undefined ? "Done" : `Show ${count.toLocaleString("en-IN")} message${count === 1 ? "" : "s"}`}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!any} onClick={() => go({ gym: "", account: "", template: "", from: "", to: "" })}>Reset</button>
      </div>
    </Sheet>
  );
}

/** One message in full: where it went from, how it went, and Meta's word on it. Never its words or who it was. */
export function MessageSheet({ m, onClose }: { m: ConsoleMessage | null; onClose: () => void }) {
  return (
    <Sheet open={m !== null} onClose={onClose} title={m?.kind_label}>
      {m && (
        <Details rows={[
          { icon: Building2, label: "Gym", value: m.gym_name },
          { icon: UserRound, label: "To", value: `${m.recipient === "member" ? "A member" : "A staff member"}, ${lastDigits(m.to_last4)}` },
          { icon: MessageCircle, label: "From", value: m.account_number ? `${m.account_number}${m.is_shared ? " (Rackline's shared number)" : ""}` : "No number to send from" },
          { icon: FileText, label: "Template", value: m.template_name ? `${m.template_name} (${m.template_language})` : "None" },
          { icon: Send, label: "Status", value: <><MessageBadge status={m.status} /> since {dayTime(m.updated_at)}</> },
          { icon: CalendarClock, label: "Written", value: `${dayTime(m.created_at)}, for ${day(m.for_date)}` },
          ...(m.delivered_at ? [{ icon: Check, label: "Delivered", value: dayTime(m.delivered_at) }] : []),
          ...(m.read_at ? [{ icon: CheckCheck, label: "Read", value: dayTime(m.read_at) }] : []),
          ...(m.attempts > 1 || m.next_retry_at ? [{ icon: RotateCw, label: "Tries", value: `${m.attempts}${m.next_retry_at ? `, next ${dayTime(m.next_retry_at)}` : ""}` }] : []),
          ...(m.error ? [{ icon: AlertCircle, label: "Why it failed", value: m.error }] : []),
          ...(m.provider_id ? [{ icon: Hash, label: "Meta's id", value: <span style={{ wordBreak: "break-all" }}>{m.provider_id}</span> }] : []),
          ...(m.billable ? [{ icon: IndianRupee, label: "Billed to the gym", value: `${rupees(m.rate_paise)} once delivered` }] : []),
        ]} />
      )}
    </Sheet>
  );
}
