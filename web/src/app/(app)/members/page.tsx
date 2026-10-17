"use client";
import { SearchX, Users } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersListInfinite } from "@/api/gen/members/members";
import type { MembersListStatus } from "@/api/gen/model";
import { usePlansList } from "@/api/gen/plans/plans";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, LoadMore, SearchField, Sheet, SkeletonRows } from "@/components/ui";
import { MemberRow } from "@/features/members-ui";
import { plural } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TrainerMember } from "@/lib/types";

const FILTERS = [
  { value: "all", label: "All" }, { value: "active", label: "Active" }, { value: "expiring", label: "Expiring" },
  { value: "due", label: "Payment due" }, { value: "expired", label: "Expired" }, { value: "frozen", label: "Frozen" },
];

/** Status, plan and branch live in the address, so coming back from a profile keeps the list as it was. */
function listUrl(f: { status: string; plan: string; branch: string }) {
  const p = new URLSearchParams();
  if (f.status !== "all") p.set("status", f.status);
  if (f.plan !== "all") p.set("plan", f.plan);
  if (f.branch !== "default") p.set("branch", f.branch);
  const s = p.toString();
  return s ? `/members?${s}` : "/members";
}

function MembersPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role, branch: homeBranch, branchName: homeBranchName } = useSession();
  const isTrainer = role.role === "trainer";
  const [f, setF] = useState({ status: params.get("status") ?? "all", plan: params.get("plan") ?? "all", branch: params.get("branch") ?? "default" });
  const [sheet, setSheet] = useState(false);
  const [q, setQ] = useState("");
  const dq = useSearch(q);

  // "default" follows the branch picked on Home; "all" or an id overrides it on this list only.
  const branches = isTrainer ? [] : role.branches;
  const branch = f.branch === "default" ? homeBranch : f.branch === "all" ? null : Number(f.branch);
  const branchName = f.branch === "default" ? homeBranchName : branch ? branches.find((b) => b.id === branch)?.name ?? "" : "All branches";
  const plans = usePlansList({ on_sale: true, limit: 100 });
  const planList = plans.data?.data.results ?? [];
  const planName = planList.find((p) => String(p.id) === f.plan)?.name;

  const apiStatus = f.status === "all" ? undefined : (f.status as MembersListStatus);
  const list = useMembersListInfinite({
    ...(dq ? { q: dq } : {}), ...(apiStatus ? { status: apiStatus } : {}),
    ...(f.plan !== "all" ? { plan: Number(f.plan) } : {}), ...(branch && !isTrainer ? { branch } : {}),
  }, { query: paged });
  const { rows, count } = pages(list);

  const set = (next: Partial<typeof f>) => { const v = { ...f, ...next }; setF(v); router.replace(listUrl(v), { scroll: false }); };
  const filtered = f.plan !== "all" || f.branch !== "default";
  const clear = () => set({ status: "all", plan: "all", branch: "default" });
  const statuses = isTrainer ? [{ value: "all", label: "All" }, { value: "attention", label: "Need attention" }, ...FILTERS.slice(1)] : FILTERS;
  const branchOptions = [
    { value: "default", label: homeBranch ? homeBranchName : "All branches" },
    ...(homeBranch ? [{ value: "all", label: "All branches" }] : []),
    ...branches.filter((b) => b.id !== homeBranch).map((b) => ({ value: String(b.id), label: b.name })),
  ];

  return (
    <div className="rl-app rl-root">
      <PageBar
        title={isTrainer ? "My Members" : "Members"} sub={isTrainer ? "Assigned to you" : branchName} back={role.role === "admin" ? "/more" : undefined}
        action={isTrainer ? undefined : <AddButton href="/members/new" label="Add Member" />}
      />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={q} onChange={setQ} placeholder="Name, phone or member ID" label="Search name, phone or member ID" filter={{ on: filtered, onClick: () => setSheet(true) }} />
          <Chips name="ml-status" label="Filter by status" value={f.status} onChange={(v) => set({ status: v })} options={statuses} />
        </div>
        <section className="rl-section" aria-label="Members">
          <div className="rl-listmeta">
            <p role="status">{list.isLoading ? "Loading…" : `Showing ${plural(rows.length, "member")}${rows.length < count ? ` of ${count}` : ""}${planName ? ` on ${planName}` : ""}`}</p>
            <p>Sorted by name</p>
          </div>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist">{rows.map((m) => <MemberRow key={m.id} m={m as unknown as TrainerMember} />)}</ul><LoadMore q={list} /></>
          ) : dq ? (
            <Empty icon={SearchX} title={`No member matches “${dq}”`} text="Check the spelling, or try their phone number or member ID.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setQ("")}>Clear Search</button>
            </Empty>
          ) : filtered || f.status !== "all" ? (
            <Empty icon={Users} title="No members match these filters" text={filtered ? "Try a different status, plan or branch." : "Nobody has this status right now."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={clear}>{filtered ? "Clear Filters" : "Show All Members"}</button>
            </Empty>
          ) : (
            <Empty icon={Users} title="No members yet" text="Members you add show up here.">
              {!isTrainer && <Link className="rl-button rl-button--block" href="/members/new">Add Member</Link>}
            </Empty>
          )}
        </section>
      </main>
      <Sheet open={sheet} onClose={() => setSheet(false)} title="Filter members">
        <p className="rl-sheet__label" style={{ marginTop: 0, marginBottom: "var(--space-2)" }}>Plan</p>
        <Chips name="ml-plan" label="Filter by plan" scroll={false} value={f.plan} onChange={(v) => set({ plan: v })}
          options={[{ value: "all", label: "All plans" }, ...planList.map((p) => ({ value: String(p.id), label: p.name }))]} />
        {branches.length > 1 && (
          <>
            <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Branch</p>
            <Chips name="ml-branch" label="Filter by branch" scroll={false} value={f.branch} onChange={(v) => set({ branch: v })} options={branchOptions} />
          </>
        )}
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--block" type="button" onClick={() => setSheet(false)}>{list.isLoading ? "Done" : `Show ${plural(count, "member")}`}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!filtered} onClick={() => set({ plan: "all", branch: "default" })}>Reset</button>
        </div>
      </Sheet>
    </div>
  );
}

export default function Page() {
  return <Suspense><MembersPage /></Suspense>;
}
