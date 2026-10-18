"use client";
import { AlertCircle, Building2, SearchX } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { PlatformGymsListOwes, PlatformGymsListStatus } from "@/api/gen/model";
import { usePlatformGymsListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, LoadMore, Photo, SearchField, Section, SkeletonRows } from "@/components/ui";
import { GymStatus } from "@/features/console/parts";
import { plural, rupees } from "@/lib/format";
import { paged, pages, useSearch } from "@/lib/hooks";

const FILTERS = [
  { value: "all", label: "All" }, { value: "active", label: "Active" }, { value: "trial", label: "Trial" }, { value: "suspended", label: "Suspended" },
  { value: "owes", label: "Owe Rackline" }, { value: "overdue", label: "Overdue" },
];
/** The money filters and what the API calls them; Home's figures open the list with them. */
const OWES: Record<string, PlatformGymsListOwes> = { owes: "any", overdue: "overdue" };

/** The address for a filter: `?status=active`, `?owes=any`, `?owes=overdue`. */
const filterUrl = (v: string) => (v === "all" ? "/console/gyms" : OWES[v] ? `/console/gyms?owes=${OWES[v]}` : `/console/gyms?status=${v}`);

function fromUrl(params: { get: (name: string) => string | null }) {
  const owes = Object.keys(OWES).find((k) => OWES[k] === params.get("owes"));
  return owes ?? params.get("status") ?? "all";
}

/** Every gym on Rackline: search, a status or money filter kept in the address, and Load More. */
function GymsPage() {
  const params = useSearchParams();
  const router = useRouter();
  const filter = fromUrl(params); // read from the address each time, so the Gyms tab clears it
  const [text, setText] = useState("");
  const q = useSearch(text);
  const list = usePlatformGymsListInfinite({
    ...(q ? { q } : {}),
    ...(OWES[filter] ? { owes: OWES[filter] } : filter !== "all" ? { status: filter as PlatformGymsListStatus } : {}),
  }, { query: paged });
  const { rows, count } = pages(list);
  const pick = (v: string) => router.replace(filterUrl(v), { scroll: false });

  return (
    <div className="rl-app rl-root">
      <PageBar title="Gyms" sub={list.data ? plural(count, "gym") : "Rackline Console"} action={<AddButton href="/console/gyms/new" label="New Gym" />} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Gym name or short name" label="Search gym name or short name" />
          <Chips name="gy-status" label="Filter gyms" value={filter} onChange={pick} options={FILTERS} />
        </div>
        <Section label="Gyms">
          {list.isLoading ? <SkeletonRows /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the gyms" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((g) => (
                  <li key={g.id}><Link className="rl-mrow" href={`/console/gyms/${g.id}`}>
                    <Photo name={g.name} />
                    <span className="rl-row__title rl-mrow__name">{g.name}</span>
                    <span className="rl-row__meta rl-mrow__meta">
                      {plural(g.branch_count, "branch", "branches")} • {g.owed_paise ? `Owes ${rupees(g.owed_paise)}` : plural(g.member_count, "member")}
                    </span>
                    <GymStatus status={g.status} />
                  </Link></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : q || filter !== "all" ? (
            <Empty icon={SearchX} title={q ? `No gym matches “${q}”` : "No gyms here"} text={q ? "Check the spelling, or try its short name." : OWES[filter] ? "No gym owes Rackline like this right now." : "No gym has this status right now."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setText(""); pick("all"); }}>Show All Gyms</button>
            </Empty>
          ) : (
            <Empty icon={Building2} title="No gyms yet" text="Add the first gym and its owner, and they can sign in at once.">
              <Link className="rl-button rl-button--block" href="/console/gyms/new">New Gym</Link>
            </Empty>
          )}
        </Section>
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><GymsPage /></Suspense>; }
