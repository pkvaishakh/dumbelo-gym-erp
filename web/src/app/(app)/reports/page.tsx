"use client";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { useReportsOverviewRetrieve } from "@/api/gen/reports/reports";
import type { ReportsOverview } from "@/api/gen/model";
import { BranchChip, PageBar } from "@/components/shell";
import { Icon, SkeletonRows } from "@/components/ui";
import { REPORTS } from "@/features/reports/categories";
import { TrendText } from "@/features/reports/parts";
import { ReportControls, useReportRange, type ReportRange } from "@/features/reports/range";
import { ReportBody } from "@/features/reports/screen";
import { ApiError } from "@/lib/api";
import { dayShort, rangeLabel, rupees, trend } from "@/lib/format";
import { CATEGORIES, changeSince, type Category } from "@/lib/reports";

type Headline = { value: string; label: string; change: { dir: "up" | "down" | "flat"; text: string } };

/** Each category's lead figure, the same one its screen opens with. */
function headline(slug: Category, o: ReportsOverview): Headline {
  const vs = (now: number, before: number) => trend(now, before, o.days);
  const n = (x: number) => x.toLocaleString("en-IN");
  switch (slug) {
    case "revenue": return { value: rupees(o.revenue.value), label: "Collected less refunds", change: vs(o.revenue.value, o.revenue.before) };
    case "expenses": return { value: rupees(o.expenses.value), label: "Spent, salaries and bills included", change: vs(o.expenses.value, o.expenses.before) };
    case "money": return { value: rupees(o.money.value), label: `Cash and bank on ${dayShort(o.to)}`, change: changeSince(o.money.value, o.money.before, o.from) };
    case "members": return { value: n(o.members.value), label: "New members", change: vs(o.members.value, o.members.before) };
    case "attendance": return { value: n(o.attendance.value), label: "Member check-ins", change: vs(o.attendance.value, o.attendance.before) };
    case "tasks": return { value: `${n(o.tasks.value)} of ${n(o.tasks.total)}`, label: "Tasks done", change: vs(o.tasks.value, o.tasks.before) };
  }
}

/** One category as a card: a link to its screen, carrying no buttons. */
function CategoryCard({ slug, name, o, search }: { slug: Category; name: string; o: ReportsOverview; search: string }) {
  const h = headline(slug, o);
  return (
    <Link className="rl-card rl-card--pad rl-report rl-pressable" href={`/reports/${slug}${search ? `?${search}` : ""}`}>
      <span style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <span className="rl-chipicon" aria-hidden="true"><Icon as={REPORTS[slug].icon} size="sm" /></span>
        <span className="rl-section__title" style={{ flex: "1 1 auto", minWidth: 0 }}>{name}</span>
        <Icon as={ChevronRight} size="sm" />
      </span>
      <span className="rl-report__value" style={{ display: "block", marginTop: "var(--space-3)" }}>{h.value}</span>
      <span className="rl-perf__label" style={{ display: "block" }}>{h.label}</span>
      <span className="rl-trend"><TrendText t={h.change} /></span>
    </Link>
  );
}

function Categories({ r }: { r: ReportRange }) {
  const q = useReportsOverviewRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  const o = q.data?.data;
  const cards = (list: typeof CATEGORIES[number][]) => o && list.map((c) => <CategoryCard key={c.slug} slug={c.slug} name={c.name} o={o} search={r.search} />);
  return (
    <ReportBody r={r} q={q} error={q.error instanceof ApiError ? q.error : null}>
      <div className="rl-app__cols">
        <div className="rl-app__col">{cards(CATEGORIES.slice(0, 3))}</div>
        <div className="rl-app__col">{cards(CATEGORIES.slice(3))}</div>
      </div>
    </ReportBody>
  );
}

function ReportsPage() {
  const r = useReportRange();
  return (
    <div className="rl-app rl-root" data-rscreen="reports">
      <PageBar title="Reports" sub={rangeLabel(r.from, r.to)} action={r.isAdmin ? <BranchChip value={r.branch} onPick={r.pickBranch} /> : undefined} />
      <main className="rl-app__main">
        <ReportControls r={r} />
        <Categories r={r} />
      </main>
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<SkeletonRows n={6} />}><ReportsPage /></Suspense>;
}
