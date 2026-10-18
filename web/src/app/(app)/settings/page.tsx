"use client";
import { Activity, MessageCircle, Phone } from "lucide-react";

import { useGymSettingsRetrieve, useGymWhatsappRetrieve } from "@/api/gen/gym/gym";
import type { GymWhatsApp } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Details, ErrorText, Section, Setting, SkeletonRows } from "@/components/ui";
import { ago, WHATSAPP_STATUS } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const SETTINGS = "/api/gym/settings/";

// The gym's own words for its WhatsApp mode (the Console's are in WHATSAPP_MODE).
const SENDS_FROM: Record<string, { label: string; note: string }> = {
  shared: { label: "Rackline's number", note: "Messages go from Rackline's WhatsApp number, billed on your Rackline plan by the message." },
  own: { label: "Your own number", note: "Messages go from your own WhatsApp Business account, and Meta bills you for them." },
  off: { label: "Not sending", note: "No WhatsApp messages go out. Ask Rackline to turn them on." },
};

/** How the gym's messages go out: set up by Rackline, so only shown here. Never a credential. */
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
        Rackline sets this up: to change it, contact Rackline.
      </p>
    </>
  );
}

/** The gym's own rules, for admins: whether members are sent their reminders, and how WhatsApp is set up. */
export default function SettingsPage() {
  const { role } = useSession();
  const q = useGymSettingsRetrieve();
  const wa = useGymWhatsappRetrieve().data?.data;
  const a = useAction();
  const gym = q.data?.data;

  async function setReminders(on: boolean) {
    try {
      await a.run(SETTINGS, { reminders_on: on }, { method: "PATCH", refresh: [SETTINGS] });
    } catch { /* shown under the switch */ }
  }

  return (
    <div className="rl-app rl-root">
      <PageBar title="Settings" sub={role.branches.length > 1 ? `For all ${role.branches.length} branches` : role.gym_name} back="/more" />
      <main className="rl-app__main">
        <Section title="Reminders to members">
          {gym ? (
            <>
              <div className="rl-card">
                <Setting
                  name="reminders"
                  title="Send reminders on WhatsApp"
                  note={gym.reminders_on ? "Renewals and payments due, at 6 am" : "Off: no one is messaged, and the desk still sees who to chase"}
                  checked={gym.reminders_on ?? true}
                  disabled={a.busy}
                  onChange={setReminders}
                />
              </div>
              <ErrorText>{a.error?.message}</ErrorText>
            </>
          ) : (
            <SkeletonRows n={1} />
          )}
        </Section>
        <p className="rl-row__meta">
          Members hear from you when their plan is a week, three days or a day from ending, and while they still owe
          money — one message a day at most. The switch takes effect at once, at every branch. To stop messaging one
          member, turn their reminders off on their profile.
        </p>
        <Section title="WhatsApp">
          {wa ? <WhatsAppCard wa={wa} /> : <SkeletonRows n={2} />}
        </Section>
      </main>
    </div>
  );
}
