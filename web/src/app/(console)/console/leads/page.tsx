"use client";
import { AlertCircle, Inbox } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { ConsoleLead, PlatformLeadsListStatus } from "@/api/gen/model";
import { usePlatformLeadsListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Chips, Empty, LoadMore, SearchField, Section, SkeletonRows } from "@/components/ui";
import { LeadRow, LeadSheet } from "@/features/console/leads";
import { plural } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";

const FILTERS = [
  { value: "new", label: "New" }, { value: "contacted", label: "Contacted" }, { value: "won", label: "Signed up" },
  { value: "lost", label: "Not now" }, { value: "all", label: "All" },
];

/** Gym owners who asked for a demo on the landing page, newest first. New ones are waiting for a call. */
function LeadsPage() {
  const params = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState(params.get("status") ?? "new");
  const [text, setText] = useState("");
  const q = useSearch(text);
  const [open, setOpen] = useState<ConsoleLead | null>(null);
  const list = usePlatformLeadsListInfinite({ ...(status !== "all" ? { status: status as PlatformLeadsListStatus } : {}), ...(q ? { q } : {}) }, { query: paged });
  const { rows, count } = pages(list);
  const pick = (v: string) => { setStatus(v); router.replace(v === "new" ? "/console/leads" : `/console/leads?status=${v}`, { scroll: false }); };
  const waiting = status === "new" && !q;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Leads" back="/console/more" sub={list.data ? (waiting ? `${count} waiting for a call` : plural(count, "lead")) : "Gyms that asked for a demo"} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Name, gym, city or number" label="Search leads" />
          <Chips name="lead-status" label="Filter by status" value={status} onChange={pick} options={FILTERS} />
        </div>
        <Section label="Leads">
          {list.isLoading ? <SkeletonRows n={4} /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the leads" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">{rows.map((l) => <LeadRow key={l.id} lead={l} onOpen={() => setOpen(l)} />)}</ul>
              <LoadMore q={list} />
            </>
          ) : q ? (
            <Empty icon={Inbox} title="No lead matches" text="Try part of the name, the gym, the city or the number.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setText("")}>Clear Search</button>
            </Empty>
          ) : (
            <Empty icon={Inbox} title={waiting ? "No one waiting" : "No leads here"}
              text={waiting ? "When a gym owner asks for a demo on the website, they show up here to call." : "No lead has this status yet."} />
          )}
        </Section>
      </main>
      <LeadSheet lead={open} onClose={() => setOpen(null)} />
    </div>
  );
}

export default function Page() { return <Suspense><LeadsPage /></Suspense>; }
