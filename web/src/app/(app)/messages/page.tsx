"use client";
import { AlertCircle, CalendarClock, IndianRupee, MessageCircle, SearchX } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";

import { useMessagesListInfinite, useMessagesUsageRetrieve } from "@/api/gen/messages/messages";
import type { GymUsage, Message } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Icon, LoadMore, SearchField, Section, SkeletonRows, Stat } from "@/components/ui";
import { GymLogFilterSheet, MessageBadge, MessageSheet } from "@/features/messages";
import { ago, day, plural, rupees } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";
import { gymLogFilters, gymLogParams, gymLogUrl, narrowedBy, type GymLogFilters } from "@/lib/messages";
import { useSession } from "@/lib/session";

const STATUSES = [
  { value: "all", label: "All" }, { value: "failed", label: "Failed" }, { value: "queued", label: "Sending" },
  { value: "sent", label: "Sent" }, { value: "delivered", label: "Delivered" }, { value: "read", label: "Read" },
];

/** What this billing month's messages on Rackline's number come to so far. A gym on its own number pays Meta. */
function Usage({ u }: { u: GymUsage }) {
  if (u.mode !== "shared") {
    return <p className="rl-row__meta">{u.mode === "own" ? "Your messages go from your own WhatsApp number, and Meta bills you for them." : "WhatsApp messages are off for your gym. Ask Rackline to turn them on."}</p>;
  }
  return (
    <>
      <div className="rl-kpis rl-kpis--pair">
        <Stat icon={IndianRupee} accent value={rupees(u.amount_paise)} label="So far this billing month" note={`${plural(u.messages, "message")} delivered`} />
        <Stat icon={CalendarClock} value={day(u.billed_on)} label="Goes on the invoice of" note={`For ${day(u.starts)} to ${day(u.ends)}`} />
      </div>
      <p className="rl-row__meta">Each message delivered from Rackline&apos;s number is billed at your plan&apos;s rate. One that never reached the phone costs nothing.</p>
    </>
  );
}

/** More → Messages: every WhatsApp message the gym has sent, newest first. Search by name or number; filter by
 *  status, message, who it went to and days. A failed one can be sent again from its sheet. */
function MessagesLog() {
  const { role } = useSession();
  const admin = role.role === "admin";
  const params = useSearchParams();
  const router = useRouter();
  const f = useMemo(() => gymLogFilters(params), [params]);
  const go = (next: Partial<GymLogFilters>) => router.replace(gymLogUrl({ ...f, ...next }), { scroll: false });
  const [text, setText] = useState("");
  const q = useSearch(text);
  const [sheet, setSheet] = useState(false);
  const [open, setOpen] = useState<Message | null>(null);
  const backwards = Boolean(f.from && f.to && f.from > f.to);
  const list = useMessagesListInfinite(gymLogParams(f, q), { query: { ...paged, enabled: !backwards } });
  const { rows, count } = pages(list);
  const usage = useMessagesUsageRetrieve({ query: { enabled: admin } }).data?.data;
  const filtered = Boolean(f.kind || f.recipient || f.from || f.to);
  const narrowed = narrowedBy(f);

  return (
    <div className="rl-app rl-root">
      <PageBar title="Messages" sub={list.data ? `${plural(count, "message")}${narrowed ? ` • ${narrowed}` : ""}` : "Every WhatsApp message sent"} back="/more" />
      <main className="rl-app__main">
        {admin && (
          <Section title="Rackline's number" aside={<span className="rl-row__meta">This billing month</span>}>
            {usage ? <Usage u={usage} /> : <SkeletonRows n={1} />}
          </Section>
        )}
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Name or number" label="Search by name or the number it went to"
            filter={{ on: filtered, onClick: () => setSheet(true) }} />
          <Chips name="messages-status" label="Filter by status" value={f.status} onChange={(v) => go({ status: v })} options={STATUSES} />
        </div>
        <Section label="Messages">
          {backwards ? (
            <Empty icon={AlertCircle} title="Those days run backwards" text="Pick a start date on or before the end date.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSheet(true)}>Change Days</button>
            </Empty>
          ) : list.isLoading ? <SkeletonRows /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the messages" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((m) => (
                  <li key={m.id}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => setOpen(m)}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={MessageCircle} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{m.to_name}</span>
                    <span className="rl-row__meta rl-mrow__meta">{m.kind_label} • {ago(m.created_at)}</span>
                    <MessageBadge status={m.status} />
                  </button></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : q || filtered || f.status !== "all" ? (
            <Empty icon={SearchX} title={q ? `No message matches “${q}”` : "No messages here"} text={q ? "Try their first name, or the last 4 digits of their number." : "Nothing was sent that fits these filters."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setText(""); router.replace("/messages", { scroll: false }); }}>Show All Messages</button>
            </Empty>
          ) : (
            <Empty icon={MessageCircle} title="No messages yet" text="Reminders, receipts and task messages show up here once your gym sends them. Switch them on in Settings." />
          )}
        </Section>
      </main>
      <GymLogFilterSheet open={sheet} onClose={() => setSheet(false)} f={f} go={go} count={list.data ? count : undefined} />
      <MessageSheet m={open} onClose={() => setOpen(null)} canRetry={admin} />
    </div>
  );
}

export default function Page() { return <Suspense><MessagesLog /></Suspense>; }
