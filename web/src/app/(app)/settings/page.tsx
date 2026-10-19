"use client";
import { Activity, AlertCircle, MessageCircle, Phone } from "lucide-react";

import { useGymMessagesList, useGymWhatsappRetrieve } from "@/api/gen/gym/gym";
import type { GymWhatsApp } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Details, Empty, ErrorText, Section, Setting, SkeletonRows } from "@/components/ui";
import { ago, WHATSAPP_STATUS } from "@/lib/format";
import { useAction } from "@/lib/hooks";
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

/** The gym's own rules, for admins: which WhatsApp messages it sends, and how WhatsApp is set up. */
export default function SettingsPage() {
  const { role } = useSession();
  const wa = useGymWhatsappRetrieve().data?.data;

  return (
    <div className="rl-app rl-root">
      <PageBar title="Settings" sub={role.branches.length > 1 ? `For all ${role.branches.length} branches` : role.gym_name} back="/more" />
      <main className="rl-app__main">
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
