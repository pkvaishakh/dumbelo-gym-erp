"use client";
import { useGymSettingsRetrieve } from "@/api/gen/gym/gym";
import { PageBar } from "@/components/shell";
import { ErrorText, Section, Setting, SkeletonRows } from "@/components/ui";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const SETTINGS = "/api/gym/settings/";

/** The gym's own rules, for admins. One switch so far: whether members are sent their reminders. */
export default function SettingsPage() {
  const { role } = useSession();
  const q = useGymSettingsRetrieve();
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
      </main>
    </div>
  );
}
