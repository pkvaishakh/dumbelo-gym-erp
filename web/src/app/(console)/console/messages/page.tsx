"use client";
import { AlertCircle, MessageCircle, SearchX } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";

import type { ConsoleMessage, PlatformMessagesListParams, PlatformMessagesListStatus } from "@/api/gen/model";
import { usePlatformGymsRetrieve, usePlatformMessagesListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Icon, LoadMore, SearchField, Section, SkeletonRows } from "@/components/ui";
import { LogFilterSheet, logUrl, MessageBadge, MessageSheet, NO_FILTERS, type LogFilters } from "@/features/console/message-log";
import { ago, plural } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";

const STATUSES = [
  { value: "all", label: "All" }, { value: "failed", label: "Failed" }, { value: "queued", label: "Sending" },
  { value: "sent", label: "Sent" }, { value: "delivered", label: "Delivered" }, { value: "read", label: "Read" },
];

/** Console → WhatsApp log: every message sent from every number, newest first. Search by number, Meta's id or the
 *  error; filter by status, gym, number, template and days. No names or words: those are the gym's. */
function MessageLog() {
  const params = useSearchParams();
  const router = useRouter();
  const f: LogFilters = useMemo(() => ({ ...NO_FILTERS, ...Object.fromEntries([...params.entries()].filter(([k]) => k in NO_FILTERS)) }), [params]);
  const go = (next: Partial<LogFilters>) => router.replace(logUrl({ ...f, ...next }), { scroll: false });
  const [text, setText] = useState("");
  const q = useSearch(text);
  const [sheet, setSheet] = useState(false);
  const [open, setOpen] = useState<ConsoleMessage | null>(null);
  const backwards = Boolean(f.from && f.to && f.from > f.to);
  const query: PlatformMessagesListParams = {
    ...(q ? { q } : {}), ...(f.status !== "all" ? { status: f.status as PlatformMessagesListStatus } : {}),
    ...(f.gym ? { gym: Number(f.gym) } : {}), ...(f.account ? { account: Number(f.account) } : {}),
    ...(f.template ? { template: Number(f.template) } : {}), ...(f.from ? { from: f.from } : {}), ...(f.to ? { to: f.to } : {}),
  };
  const list = usePlatformMessagesListInfinite(query, { query: { ...paged, enabled: !backwards } });
  const { rows, count } = pages(list);
  const gym = usePlatformGymsRetrieve(Number(f.gym), { query: { enabled: Boolean(f.gym) } });
  const gymName = gym.data?.data.name;
  const filtered = Boolean(f.gym || f.account || f.template || f.from || f.to);
  const narrowedBy = [gymName, f.account && "one number", f.template && "one template", (f.from || f.to) && "some days"].filter(Boolean).join(", ");

  return (
    <div className="rl-app rl-root">
      <PageBar title="WhatsApp log" sub={list.data ? `${plural(count, "message")}${narrowedBy ? ` • ${narrowedBy}` : ""}` : "Every message sent"} back="/console/more" />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Number, Meta id or error" label="Search by the number it went to, Meta's id or the error"
            filter={{ on: filtered, onClick: () => setSheet(true) }} />
          <Chips name="log-status" label="Filter by status" value={f.status} onChange={(v) => go({ status: v })} options={STATUSES} />
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
                    <span className="rl-row__title rl-mrow__name">{m.kind_label}</span>
                    <span className="rl-row__meta rl-mrow__meta">{m.gym_name} • {ago(m.created_at)}</span>
                    <MessageBadge status={m.status} />
                  </button></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : q || filtered || f.status !== "all" ? (
            <Empty icon={SearchX} title={q ? `No message matches “${q}”` : "No messages here"} text={q ? "Try the last 4 digits of the number, or more of Meta's id." : "Nothing was sent that fits these filters."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setText(""); router.replace("/console/messages", { scroll: false }); }}>Show All Messages</button>
            </Empty>
          ) : (
            <Empty icon={MessageCircle} title="No messages yet" text="Reminders, receipts and task messages show up here once gyms start sending them." />
          )}
        </Section>
        <p className="rl-row__meta">Names and what each message said stay with the gym. Rackline sees them only in a support window the gym&apos;s admin gives.</p>
      </main>
      <LogFilterSheet open={sheet} onClose={() => setSheet(false)} f={f} go={go} gymName={gymName} count={list.data ? count : undefined} />
      <MessageSheet m={open} onClose={() => setOpen(null)} />
    </div>
  );
}

export default function Page() { return <Suspense><MessageLog /></Suspense>; }
