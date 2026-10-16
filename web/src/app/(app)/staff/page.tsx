"use client";
import { UserPlus, Users } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useStaffList } from "@/api/gen/staff/staff";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Icon, Photo, Section, SkeletonRows, Status } from "@/components/ui";
import { plural } from "@/lib/format";
import { useSession } from "@/lib/session";

function StaffPage() {
  const params = useSearchParams();
  const roleName = params.get("role") === "receptionist" ? "receptionist" : "trainer";
  const { role } = useSession();
  const [branch, setBranch] = useState("all");
  const q = useStaffList({ role: roleName, limit: 100 });
  const all = q.data?.data.results ?? [];
  const rows = all.filter((s) => branch === "all" || s.branches.includes(Number(branch)));
  const title = roleName === "trainer" ? "Trainers" : "Receptionists";
  const bname = (id: number) => role.branches.find((b) => b.id === id)?.name ?? "";
  return (
    <div className="rl-app rl-root">
      <PageBar title={title} sub={`${plural(all.filter((s) => s.is_active).length, "active " + roleName)}`} back="/more" />
      <main className="rl-app__main">
        <Section label="Add">
          <Link className="rl-button rl-button--block" href={`/staff/new?role=${roleName}`}><Icon as={UserPlus} />Add {roleName === "trainer" ? "Trainer" : "Receptionist"}</Link>
        </Section>
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
          ) : <Empty icon={Users} title={`No ${title.toLowerCase()} yet`} text="Add them so they can sign in and you can give them tasks." />}
        </Section>
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><StaffPage /></Suspense>; }
