"use client";
import { AlertCircle, CalendarClock, Clock, FileText } from "lucide-react";
import { useState } from "react";

import { usePlatformAutomationRetrieve } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Details, Empty, Section, SkeletonRows } from "@/components/ui";
import { AutomationSheet } from "@/features/console/messages";
import { ago } from "@/lib/format";
import { daysLabel, hourLabel } from "@/lib/messages";

/** Console → Automation: when Dumbelo's jobs run for every gym. A gym with its own times (set on its screen) keeps
 *  them. Changes apply on each job's next run, with nothing to restart. */
export default function Automation() {
  const q = usePlatformAutomationRetrieve();
  const s = q.data?.data;
  const [editing, setEditing] = useState(false);
  return (
    <div className="rl-app rl-root">
      <PageBar title="Automation" sub="When messages and invoices go out" back="/console/more" />
      <main className="rl-app__main">
        {q.isLoading ? <SkeletonRows n={3} /> : q.isError || !s ? (
          <Empty icon={AlertCircle} title="Can't load the times" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
          </Empty>
        ) : (
          <>
            <Section title="Reminders to members">
              <Details rows={[
                { icon: Clock, label: "Go out at", value: `${hourLabel(s.reminder_hour)}, on each gym's clock` },
                { icon: CalendarClock, label: "Plan ending soon", value: `${daysLabel(s.days_ahead)} before it ends` },
              ]} />
            </Section>
            <Section title="Dumbelo invoices">
              <Details rows={[{ icon: FileText, label: "Written on a billing day at", value: hourLabel(s.invoice_hour) }]} />
            </Section>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" aria-haspopup="dialog" onClick={() => setEditing(true)}>Edit Times</button>
            <p className="rl-row__meta">
              Changes apply on each job&apos;s next run: within 15 minutes for reminders, an hour for invoices. Retry waits are
              fixed by Meta&apos;s limits. A gym with its own times keeps them; set those on the gym&apos;s screen.
              {s.updated_at ? ` Last changed ${ago(s.updated_at)}${s.updated_by_name ? ` by ${s.updated_by_name}` : ""}.` : ""}
            </p>
            <AutomationSheet schedule={s} open={editing} onClose={() => setEditing(false)} />
          </>
        )}
      </main>
    </div>
  );
}
