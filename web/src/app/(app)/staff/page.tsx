"use client";
import { SearchX, Users } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useStaffList } from "@/api/gen/staff/staff";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, Photo, SearchField, Section, SkeletonRows, Status } from "@/components/ui";
import { plural } from "@/lib/format";
import { useSession } from "@/lib/session";

function StaffPage() {
  const params = useSearchParams();
  const roleName = params.get("role") === "receptionist" ? "receptionist" : "trainer";
  const { role } = useSession();
  const [branch, setBranch] = useState("all");
  const [search, setSearch] = useState("");
  const q = useStaffList({ role: roleName, limit: 100 });
  const all = q.data?.data.results ?? [];
  // The whole list is already here, so search runs in the browser: name, username, phone or email.
  const needle = search.trim().toLowerCase();
  const digits = needle.replace(/\D/g, "");
  const matches = (s: (typeof all)[number]) => !needle || s.name.toLowerCase().includes(needle) || (s.username ?? "").includes(needle.replace(/^@/, "")) || (s.email ?? "").toLowerCase().includes(needle)
    || (digits.length > 0 && (s.phone ?? "").replace(/\D/g, "").includes(digits));
  const rows = all.filter((s) => (branch === "all" || s.branches.includes(Number(branch))) && matches(s));
  const title = roleName === "trainer" ? "Trainers" : "Receptionists";
  const addLabel = `Add ${roleName === "trainer" ? "Trainer" : "Receptionist"}`;
  const bname = (id: number) => role.branches.find((b) => b.id === id)?.name ?? "";
  return (
    <div className="rl-app rl-root">
      <PageBar title={title} sub={`${plural(all.filter((s) => s.is_active).length, "active " + roleName)}`} back="/more"
        action={<AddButton href={`/staff/new?role=${roleName}`} label={addLabel} />} />
      <main className="rl-app__main">
        <div className="rl-searchbar">
          <SearchField value={search} onChange={setSearch} placeholder="Name, phone or email" label="Search name, phone or email" />
        </div>
        <Section label={title}>
          <Chips name="st-branch" label="Branch" value={branch} onChange={setBranch} style={{ marginTop: 0 }}
            options={[{ value: "all", label: "All branches", count: all.length }, ...role.branches.map((b) => ({ value: String(b.id), label: b.name, count: all.filter((s) => s.branches.includes(b.id)).length }))]} />
          {q.isLoading ? <SkeletonRows /> : rows.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact" style={{ marginTop: "var(--space-3)" }}>
              {rows.map((s) => (
                <li key={s.id}><Link className="rl-mrow" href={`/staff/${s.id}`}>
                  <Photo name={s.name} />
                  <span className="rl-row__title rl-mrow__name">{s.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{s.branches.map(bname).join(", ")}{s.shift ? ` • ${s.shift}` : ""}</span>
                  {!s.is_active && <Status status="off" />}
                </Link></li>
              ))}
            </ul>
          ) : needle ? (
            <Empty icon={SearchX} title={`No one matches “${search.trim()}”`} text="Check the spelling, or try their phone number or email.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setSearch("")}>Clear Search</button>
            </Empty>
          ) : (
            <Empty icon={Users} title={`No ${title.toLowerCase()} yet`} text="Add them so they can sign in and you can give them tasks.">
              <Link className="rl-button rl-button--block" href={`/staff/new?role=${roleName}`}>{addLabel}</Link>
            </Empty>
          )}
        </Section>
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><StaffPage /></Suspense>; }
