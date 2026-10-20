"use client";
/* Gym owners who asked for a demo on the landing page: a row for the list, and the sheet to call them and move
 * the lead along. */
import { Building2, CalendarDays, Mail, Megaphone, MessageCircle, MessageSquare, Phone as PhoneIcon, UserRound } from "lucide-react";

import type { ConsoleLead, LeadStatusEnum } from "@/api/gen/model";
import { Details, ErrorText, Icon, Photo, Sheet } from "@/components/ui";
import { ago, dayTime, LEAD_STATUS, phone } from "@/lib/format";
import { useAction } from "@/lib/hooks";

const REFRESH = ["/api/platform/leads/", "/api/platform/summary/"];
const NEXT: { status: LeadStatusEnum; label: string }[] = [
  { status: "contacted", label: "Mark Contacted" }, { status: "won", label: "Mark Signed Up" }, { status: "lost", label: "Mark Not Now" },
];

export function LeadStatus({ status }: { status: string }) {
  const s = LEAD_STATUS[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

export function LeadRow({ lead, onOpen }: { lead: ConsoleLead; onOpen: () => void }) {
  return (
    <li><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={onOpen}>
      <Photo name={lead.gym_name} />
      <span className="rl-row__title rl-mrow__name">{lead.gym_name}</span>
      <span className="rl-row__meta rl-mrow__meta">{lead.name} • {lead.city} • {ago(lead.created_at)}</span>
      <LeadStatus status={lead.status ?? "new"} />
    </button></li>
  );
}

/** Where a lead came from, in words: "google / cpc, kerala-gyms", or nothing when the page had no tags. */
function cameFrom(l: ConsoleLead) {
  const source = [l.utm_source, l.utm_medium].filter(Boolean).join(" / ");
  return [source, l.utm_campaign].filter(Boolean).join(", ");
}

export function LeadSheet({ lead, onClose }: { lead: ConsoleLead | null; onClose: () => void }) {
  const a = useAction();
  const close = () => { a.clearError(); onClose(); };
  async function move(status: LeadStatusEnum) {
    try { await a.run(`/api/platform/leads/${lead!.id}/status/`, { status }, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  const digits = lead?.phone.replace(/\D/g, "") ?? "";
  const source = lead ? cameFrom(lead) : "";
  return (
    <Sheet open={!!lead} onClose={close} title={lead?.gym_name}>
      {lead && (
        <>
          <Details rows={[
            { icon: UserRound, label: "Asked by", value: lead.name },
            { icon: PhoneIcon, label: "Mobile number", value: phone(lead.phone) },
            ...(lead.email ? [{ icon: Mail, label: "Email", value: lead.email }] : []),
            { icon: Building2, label: "Gym", value: `${lead.city} • ${lead.branches_label}` },
            ...(lead.note ? [{ icon: MessageSquare, label: "Their note", value: lead.note }] : []),
            ...(source ? [{ icon: Megaphone, label: "Came from", value: source }] : []),
            { icon: CalendarDays, label: "Asked", value: dayTime(lead.created_at) },
            ...(lead.status_at ? [{ icon: CalendarDays, label: `${LEAD_STATUS[lead.status ?? "new"]?.label ?? "Changed"} by ${lead.status_by_name ?? "Dumbelo"}`, value: dayTime(lead.status_at) }] : []),
          ]} />
          <div className="rl-sheet__actions">
            <a className="rl-button rl-button--block" href={`tel:+${digits}`}><Icon as={PhoneIcon} size="sm" />Call {lead.name.split(" ")[0]}</a>
            <a className="rl-button rl-button--secondary rl-button--block" href={`https://wa.me/${digits}`} target="_blank" rel="noopener noreferrer">
              <Icon as={MessageCircle} size="sm" />Message on WhatsApp
            </a>
          </div>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            {NEXT.filter((n) => n.status !== lead.status).map((n) => (
              <button key={n.status} className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={() => move(n.status)}>{n.label}</button>
            ))}
          </div>
        </>
      )}
    </Sheet>
  );
}
