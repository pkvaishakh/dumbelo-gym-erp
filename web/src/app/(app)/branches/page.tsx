"use client";
import { Building2, Plus } from "lucide-react";
import Link from "next/link";

import { useBillingPlanRetrieve } from "@/api/gen/billing/billing";
import { useBranchesList } from "@/api/gen/branches/branches";
import { PageBar } from "@/components/shell";
import { Icon, Section, SkeletonRows, Status } from "@/components/ui";
import { branchesOf, plural, span } from "@/lib/format";

export default function BranchesPage() {
  const q = useBranchesList({ limit: 50 });
  const rows = q.data?.data.results ?? [];
  const plan = useBillingPlanRetrieve().data?.data;
  const full = plan ? plan.branches_in_use >= plan.branch_quota : false;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Branches" sub={plan ? `${branchesOf(plan.branches_in_use, plan.branch_quota)} open` : plural(rows.length, "branch", "branches")} back="/more" />
      <main className="rl-app__main">
        {full && plan ? (
          <Section label="Your plan is full">
            <div className="rl-card rl-card--pad">
              <p className="rl-row__title" style={{ margin: 0 }}>Your plan has room for {plural(plan.branch_quota, "branch", "branches")}</p>
              <p className="rl-row__meta">
                {plan.branch_quota === 1 ? "It's open" : `All ${plan.branch_quota} are open`}. To open another, ask Rackline to add one to
                your plan, or close a branch first.
              </p>
              <Link className="rl-button rl-button--block" href="/rackline-plan"><Icon as={Plus} />Add Branch to My Plan</Link>
            </div>
          </Section>
        ) : (
          <Section label="Add"><Link className="rl-button rl-button--block" href="/branches/new"><Icon as={Plus} />Add Branch</Link></Section>
        )}
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
