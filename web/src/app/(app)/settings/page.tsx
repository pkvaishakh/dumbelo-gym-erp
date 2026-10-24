"use client";
import { Activity, AlertCircle, MessageCircle, Phone } from "lucide-react";
import { useState } from "react";

import { useGymMessagesList, useGymWhatsappRetrieve } from "@/api/gen/gym/gym";
import type { GymWhatsApp } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Details, Empty, ErrorText, Field, Section, Setting, SkeletonRows } from "@/components/ui";
import { ago, WHATSAPP_STATUS } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { MESSAGE_TO, whenLabel } from "@/lib/messages";
import { useSession } from "@/lib/session";

const MESSAGES = "/api/gym/messages/";

// The gym's own words for its WhatsApp mode (the Console's are in WHATSAPP_MODE).
const SENDS_FROM: Record<string, { label: string; note: string }> = {
  shared: { label: "Dumbelo's number", note: "Messages go from Dumbelo's WhatsApp number, billed on your Dumbelo plan by the message." },
  own: { label: "Your own number", note: "Messages go from your own WhatsApp Business account, and Meta bills you for them." },
  off: { label: "Not sending", note: "No WhatsApp messages go out. Ask Dumbelo to turn them on." },
};

/** How the gym's messages go out: set up by Dumbelo, so only shown here. Never a credential. */
function WhatsAppCard({ wa }: { wa: GymWhatsApp }) {
  const from = SENDS_FROM[wa.mode] ?? { label: wa.mode, note: "" };
  const status = WHATSAPP_STATUS[wa.status] ?? { label: wa.status, badge: "frozen" };
  return (
    <>
      <Details rows={[
        { icon: MessageCircle, label: "Sends from", value: from.label },
        ...(wa.mode !== "off" ? [{ icon: Phone, label: "Number", value: wa.number ? `${wa.number}${wa.verified_name ? ` • ${wa.verified_name}` : ""}` : "Not set up yet" }] : []),
        {
          icon: Activity, label: wa.checked_at ? `Status, checked ${ago(wa.checked_at)}` : "Status",
          value: <span className={`rl-status rl-status--${status.badge}`}>{status.label}</span>,
        },
      ]} />
      <p className="rl-row__meta">
        {from.note} {wa.status === "failing" || wa.status === "not_set_up" ? "Until it works, the desk still sees who to chase on the reminders list. " : ""}
        Dumbelo sets this up: to change it, contact Dumbelo.
      </p>
    </>
  );
}

/** A switch per message the gym sends (Pause / Resume). When each goes out is Dumbelo's to set, so it's only said. */
function MessageSwitches() {
  const q = useGymMessagesList();
  const a = useAction();
  async function turn(kind: string, on: boolean) {
    try {
      await a.run(`${MESSAGES}${kind}/`, { is_on: on }, { method: "PATCH", refresh: [MESSAGES] });
    } catch { /* shown under the switches */ }
  }
  if (q.isLoading) return <SkeletonRows n={5} />;
  if (q.isError || !q.data) {
    return (
      <Empty icon={AlertCircle} title="Can't load your messages" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
      </Empty>
    );
  }
  return (
    <>
      <div className="rl-card">
        {q.data.data.map((r) => (
          <Setting key={r.kind} name={`message-${r.kind}`} title={r.label} checked={r.is_on} disabled={a.busy} onChange={(on) => turn(r.kind, on)}
            note={`${MESSAGE_TO[r.kind] ?? ""} • ${whenLabel(r)}${r.is_on ? "" : " • Paused"}`} />
        ))}
      </div>
      <ErrorText>{a.error?.message}</ErrorText>
    </>
  );
}

const MONTHS = [{ value: "0", label: "A calendar month" }, { value: "28", label: "28 days" }, { value: "30", label: "30 days" }, { value: "other", label: "Another number of days" }];

/** How long a plan's month runs at this gym: calendar months, or a number of days that every plan's months count in. */
function MonthLength({ days }: { days: number }) {
  const known = MONTHS.some((m) => m.value === String(days));
  const [pick, setPick] = useState(known ? String(days) : "other");
  const [other, setOther] = useState(known ? "" : String(days));
  const a = useAction();
  const chosen = pick === "other" ? Number(other) || 0 : Number(pick);
  async function save() {
    try { await a.run("/api/gym/settings/", { month_days: chosen }, { method: "PATCH" }); } catch { /* shown */ }
  }
  return (
    <div className="rl-card rl-card--pad">
      <div className="rl-form">
        <Field label="A month is">{(id) => (
          <select className="rl-field__input" id={id} value={pick} onChange={(e) => { setPick(e.target.value); a.clearError(); }}>
            {MONTHS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        )}</Field>
        {pick === "other" && (
          <Field label="Days in a month" error={fieldError(a.error, "month_days")}>{(id) => (
            <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={1} max={60} value={other} placeholder="31" onChange={(e) => setOther(e.target.value)} />
          )}</Field>
        )}
        <p className="rl-field__hint" style={{ margin: 0 }}>
          {chosen ? `A 3-month plan runs ${3 * chosen} days.` : "A month from 14 Oct runs to 13 Nov."} Plans sold from now on follow it; plans already sold keep their dates.
        </p>
      </div>
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy || chosen === days || (pick === "other" && !chosen)} onClick={save}>
          {a.busy ? "Saving…" : "Save Month Length"}
        </button>
      </div>
    </div>
  );
}

/** The gym's own rules, for admins: how long a plan's month runs, which WhatsApp messages it sends, and how WhatsApp is set up. */
export default function SettingsPage() {
  const { role } = useSession();
  const wa = useGymWhatsappRetrieve().data?.data;

  return (
    <div className="rl-app rl-root">
      <PageBar title="Settings" sub={role.branches.length > 1 ? `For all ${role.branches.length} branches` : role.gym_name} back="/more" />
      <main className="rl-app__main">
        <Section title="Plans">
          <MonthLength key={role.month_days} days={role.month_days} />
        </Section>
        <Section title="Messages" aside={<span className="rl-row__meta">Times set by Dumbelo</span>}>
          <MessageSwitches />
        </Section>
        <p className="rl-row__meta">
          Pause a message and it stops at once, at every branch; the desk still sees who to chase on the reminders list.
          Members get one reminder a day at most. Dumbelo sets when messages go out, on your gym&apos;s clock. To stop
          messaging one member, turn their reminders off on their profile.
        </p>
        <Section title="WhatsApp">
          {wa ? <WhatsAppCard wa={wa} /> : <SkeletonRows n={2} />}
        </Section>
      </main>
    </div>
  );
}
