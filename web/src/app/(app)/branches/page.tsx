"use client";
import { Building2, Plus } from "lucide-react";
import Link from "next/link";

import { useBranchesList } from "@/api/gen/branches/branches";
import { PageBar } from "@/components/shell";
import { Icon, Section, SkeletonRows, Status } from "@/components/ui";
import { span } from "@/lib/format";

export default function BranchesPage() {
  const q = useBranchesList({ limit: 50 });
  const rows = q.data?.data.results ?? [];
  return (
    <div className="rl-app rl-root">
      <PageBar title="Branches" sub={`${rows.length} branches`} back="/more" />
      <main className="rl-app__main">
        <Section label="Add"><Link className="rl-button rl-button--block" href="/branches/new"><Icon as={Plus} />Add Branch</Link></Section>
        <Section label="Branches">
          {q.isLoading ? <SkeletonRows n={4} /> : (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((b) => (
                <li key={b.id}><Link className="rl-mrow" href={`/branches/${b.id}/edit`}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Building2} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{b.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{b.sessions.map((s) => `${s.name} ${span(s.starts, s.ends)}`).join(" • ") || "No opening hours"}</span>
                  {!b.is_active && <Status status="off" />}
                </Link></li>
              ))}
            </ul>
          )}
        </Section>
      </main>
    </div>
  );
}
