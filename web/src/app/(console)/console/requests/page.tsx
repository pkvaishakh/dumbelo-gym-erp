"use client";
import { AlertCircle, Inbox } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { ConsoleBranchAsk, PlatformBranchRequestsListStatus } from "@/api/gen/model";
import { usePlatformBranchRequestsListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Chips, Empty, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { RequestRow, RequestSheet } from "@/features/console/requests";
import { plural } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

const FILTERS = [
  { value: "asked", label: "Waiting" }, { value: "approved", label: "Approved" }, { value: "declined", label: "Declined" }, { value: "all", label: "All" },
];

/** Gyms asking for room for more branches, the waiting ones first. The filter is kept in the address. */
function RequestsPage() {
  const params = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState(params.get("status") ?? "asked");
  const [open, setOpen] = useState<ConsoleBranchAsk | null>(null);
  const list = usePlatformBranchRequestsListInfinite(status !== "all" ? { status: status as PlatformBranchRequestsListStatus } : {}, { query: paged });
  const { rows, count } = pages(list);
  const pick = (v: string) => { setStatus(v); router.replace(v === "asked" ? "/console/requests" : `/console/requests?status=${v}`, { scroll: false }); };
  const waiting = status === "asked";
  return (
    <div className="rl-app rl-root">
      <PageBar title="Branch requests" sub={list.data ? (waiting ? `${count} waiting` : plural(count, "request")) : "Gyms asking for more branches"} />
      <main className="rl-app__main">
        <Chips name="rq-status" label="Filter by status" value={status} onChange={pick} options={FILTERS} />
        <Section label="Requests">
          {list.isLoading ? <SkeletonRows n={3} /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the requests" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">{rows.map((r) => <RequestRow key={r.id} r={r} showGym onOpen={() => setOpen(r)} />)}</ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={Inbox} title={waiting ? "Nothing waiting" : "No requests here"}
              text={waiting ? "When a gym's admin taps Add Branch to My Plan, it shows up here to approve." : "No request has this status yet."} />
          )}
        </Section>
      </main>
      <RequestSheet r={open} onClose={() => setOpen(null)} />
    </div>
  );
}

export default function Page() { return <Suspense><RequestsPage /></Suspense>; }
