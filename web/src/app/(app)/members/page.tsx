"use client";
import { SearchX, Users } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersListInfinite } from "@/api/gen/members/members";
import type { MembersListStatus } from "@/api/gen/model";
import { usePlansList } from "@/api/gen/plans/plans";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, LoadMore, SearchField, SkeletonRows } from "@/components/ui";
import { ActiveFilters, DEFAULT_SORT, MemberFilterSheet, type MemberFilters, SHEET_DEFAULTS, SORTS, sortOf } from "@/features/member-filters";
import { MemberRow } from "@/features/members-ui";
import { plural } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TrainerMember } from "@/lib/types";

const FILTERS = [
  { value: "all", label: "All" }, { value: "active", label: "Active" }, { value: "expiring", label: "Expiring" },
  { value: "due", label: "Payment due" }, { value: "expired", label: "Expired" }, { value: "frozen", label: "Frozen" },
];

/** The filters live in the address, so coming back from a profile keeps the list as it was. */
function listUrl(f: MemberFilters) {
  const p = new URLSearchParams();
  if (f.status !== "all") p.set("status", f.status);
  for (const k of ["plan", "workout", "diet", "branch"] as const) if (f[k] !== SHEET_DEFAULTS[k]) p.set(k, f[k]);
  if (f.sort !== DEFAULT_SORT) p.set("sort", f.sort);
  const s = p.toString();
  return s ? `/members?${s}` : "/members";
}

function MembersPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role, branch: homeBranch, branchName: homeBranchName } = useSession();
  const isTrainer = role.role === "trainer";
  const isAdmin = role.role === "admin";
  const [f, setF] = useState<MemberFilters>({
    status: params.get("status") ?? "all", plan: params.get("plan") ?? "all", branch: params.get("branch") ?? "default",
    workout: params.get("workout") ?? "all", diet: params.get("diet") ?? "all", sort: sortOf(params.get("sort")),
  });
  const [sheet, setSheet] = useState(false);
  const [q, setQ] = useState("");
  const dq = useSearch(q);

  // Admins only: "default" follows the branch picked on Home; "all" or an id overrides it on this list only.
  // Everyone else sees all of their own branches, which the API already keeps them to.
  const branches = isAdmin ? role.branches : [];
  const branch = !isAdmin ? null : f.branch === "default" ? homeBranch : f.branch === "all" ? null : Number(f.branch);
  const branchName = !isAdmin || f.branch === "default" ? homeBranchName : branch ? branches.find((b) => b.id === branch)?.name ?? "" : "All branches";
  const plans = usePlansList({ on_sale: true, limit: 100 });
  const planList = plans.data?.data.results ?? [];
  const planOptions = [{ value: "all", label: "All plans" }, ...planList.map((p) => ({ value: String(p.id), label: p.name }))];

  const apiStatus = f.status === "all" ? undefined : (f.status as MembersListStatus);
  const list = useMembersListInfinite({
    ...(dq ? { q: dq } : {}), ...(apiStatus ? { status: apiStatus } : {}),
    ...(f.plan !== "all" ? { plan: Number(f.plan) } : {}), ...(branch ? { branch } : {}),
    ...(f.workout !== "all" ? { workout: f.workout } : {}), ...(f.diet !== "all" ? { diet: f.diet } : {}), sort: f.sort,
  }, { query: paged });
  const { rows, count } = pages(list);

  const set = (next: Partial<MemberFilters>) => { const v = { ...f, ...next }; setF(v); router.replace(listUrl(v), { scroll: false }); };
  const filtered = f.plan !== "all" || f.workout !== "all" || f.diet !== "all" || (isAdmin && f.branch !== "default");
  const clear = () => set({ status: "all", ...SHEET_DEFAULTS });
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
          <SearchField value={q} onChange={setQ} placeholder="Name, phone or member ID" label="Search name, phone or member ID" filter={{ on: filtered || f.sort !== DEFAULT_SORT, onClick: () => setSheet(true) }} />
          <Chips name="ml-status" label="Filter by status" value={f.status} onChange={(v) => set({ status: v })} options={statuses} />
        </div>
        <section className="rl-section" aria-label="Members">
          <ActiveFilters f={f} set={set} plans={planOptions} branches={branchOptions} />
          <div className="rl-listmeta">
            <p role="status">{list.isLoading ? "Loading…" : `Showing ${plural(rows.length, "member")}${rows.length < count ? ` of ${count}` : ""}`}</p>
            <p>{SORTS.find((s) => s.value === f.sort)?.meta}</p>
          </div>
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist">{rows.map((m) => <MemberRow key={m.id} m={m as unknown as TrainerMember} />)}</ul><LoadMore q={list} /></>
          ) : dq ? (
            <Empty icon={SearchX} title={`No member matches “${dq}”`} text="Check the spelling, or try their phone number or member ID.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setQ("")}>Clear Search</button>
            </Empty>
          ) : filtered || f.status !== "all" ? (
            <Empty icon={Users} title="No members match these filters" text={filtered ? "Take a filter off, or try another." : "Nobody has this status right now."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={clear}>{filtered ? "Clear Filters" : "Show All Members"}</button>
            </Empty>
          ) : (
            <Empty icon={Users} title="No members yet" text="Members you add show up here.">
              {!isTrainer && <Link className="rl-button rl-button--block" href="/members/new">Add Member</Link>}
            </Empty>
          )}
        </section>
      </main>
      <MemberFilterSheet open={sheet} onClose={() => setSheet(false)} f={f} set={set} plans={planOptions} branches={branchOptions}
        count={count} loading={list.isLoading} />
    </div>
  );
}

export default function Page() {
  return <Suspense><MembersPage /></Suspense>;
}
