"use client";
import { SearchX, Users } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersListInfinite } from "@/api/gen/members/members";
import type { MembersListStatus } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Chips, Empty, LoadMore, SearchField, SkeletonRows } from "@/components/ui";
import { MemberRow } from "@/features/members-ui";
import { plural } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TrainerMember } from "@/lib/types";

const FILTERS = [
  { value: "all", label: "All" }, { value: "active", label: "Active" }, { value: "expiring", label: "Expiring" },
  { value: "due", label: "Payment due" }, { value: "expired", label: "Expired" }, { value: "frozen", label: "Frozen" },
];

function MembersPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role, branch, branchName } = useSession();
  const isTrainer = role.role === "trainer";
  const [status, setStatus] = useState(params.get("status") ?? "all");
  const [q, setQ] = useState("");
  const dq = useSearch(q);
  const apiStatus = status === "all" ? undefined : (status as MembersListStatus);
  const list = useMembersListInfinite({ ...(dq ? { q: dq } : {}), ...(apiStatus ? { status: apiStatus } : {}), ...(branch && !isTrainer ? { branch } : {}) }, { query: paged });
  const { rows, count } = pages(list);
  const pick = (v: string) => { setStatus(v); router.replace(v === "all" ? "/members" : `/members?status=${v}`, { scroll: false }); };
  const filters = isTrainer ? [{ value: "all", label: "All" }, { value: "attention", label: "Need attention" }, ...FILTERS.slice(1)] : FILTERS;
  return (
    <div className="rl-app rl-root">
      <PageBar title={isTrainer ? "My Members" : "Members"} sub={isTrainer ? "Assigned to you" : branchName} back={role.role === "admin" ? "/more" : undefined} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={q} onChange={setQ} placeholder="Name, phone or member ID" label="Search name, phone or member ID" />
          <Chips name="ml-status" label="Filter by status" value={status} onChange={pick} options={filters} />
        </div>
        <section className="rl-section" aria-label="Members">
          {!isTrainer && (
            <div style={{ marginBottom: "var(--space-3)" }}><Link className="rl-button rl-button--secondary rl-button--block" href="/members/new">Add Member</Link></div>
          )}
          <div className="rl-listmeta"><p role="status">{list.isLoading ? "Loading…" : `Showing ${plural(rows.length, "member")}${rows.length < count ? ` of ${count}` : ""}`}</p><p>Sorted by name</p></div>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist">{rows.map((m) => <MemberRow key={m.id} m={m as unknown as TrainerMember} />)}</ul><LoadMore q={list} /></>
          ) : dq ? (
            <Empty icon={SearchX} title={`No member matches “${dq}”`} text="Check the spelling, or try their phone number or member ID.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setQ("")}>Clear Search</button>
            </Empty>
          ) : (
            <Empty icon={Users} title={status === "all" ? "No members yet" : "No members here"} text={status === "all" ? "Members you add show up here." : "Nobody has this status right now."}>
              {status !== "all" && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => pick("all")}>Show All Members</button>}
            </Empty>
          )}
        </section>
      </main>
    </div>
  );
}

export default function Page() {
  return <Suspense><MembersPage /></Suspense>;
}
