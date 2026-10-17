"use client";
import { endOfMonth, parseISO, startOfMonth, subMonths } from "date-fns";
import { Receipt, SearchX } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useExpensesListInfinite } from "@/api/gen/expenses/expenses";
import type { ExpensesListCategory, ExpensesListMethod } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, Field, Icon, LoadMore, SearchField, Section, Sheet, SkeletonRows, Stat } from "@/components/ui";
import { day, isoDate, plural, rangeLabel, rupees } from "@/lib/format";
import { paged, pages, useGet, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const CATEGORIES: Record<string, string> = { rent: "Rent", salaries: "Salaries", utilities: "Utilities", equipment: "Equipment", maintenance: "Maintenance", supplies: "Supplies", marketing: "Marketing", other: "Other" };
const METHODS: Record<string, string> = { cash: "Cash", upi: "UPI", card: "Card", bank: "Bank transfer" };

type Period = "month" | "last" | "3m" | "fy" | "custom";
const PERIODS: { value: Period; label: string }[] = [
  { value: "month", label: "This month" }, { value: "last", label: "Last month" }, { value: "3m", label: "3 months" },
  { value: "fy", label: "Financial year" }, { value: "custom", label: "Custom" },
];

/** The first and last day a period covers. Months are whole calendar months; the financial year starts 1 April. */
function rangeOf(period: Period, today: string, from: string | null, to: string | null): [string, string] {
  const t = parseISO(today);
  if (period === "last") { const m = subMonths(t, 1); return [isoDate(startOfMonth(m)), isoDate(endOfMonth(m))]; }
  if (period === "3m") return [isoDate(startOfMonth(subMonths(t, 2))), today];
  if (period === "fy") return [`${t.getMonth() < 3 ? t.getFullYear() - 1 : t.getFullYear()}-04-01`, today];
  if (period === "custom") return [from || isoDate(startOfMonth(t)), to || today];
  return [isoDate(startOfMonth(t)), today];
}

type Filters = { period: Period; from: string; to: string; category: string; branch: string; method: string };

/** Filters live in the address, so Back and a shared link keep the list as it was. */
function listUrl(f: Filters) {
  const p = new URLSearchParams();
  if (f.period !== "month") p.set("period", f.period);
  if (f.period === "custom") { p.set("from", f.from); p.set("to", f.to); }
  if (f.category !== "all") p.set("category", f.category);
  if (f.branch !== "default") p.set("branch", f.branch);
  if (f.method !== "all") p.set("method", f.method);
  const s = p.toString();
  return s ? `/expenses?${s}` : "/expenses";
}

function ExpensesPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role, branch: homeBranch, branchName: homeBranchName } = useSession();
  const today = isoDate(new Date());
  const asked = params.get("period");
  const period = (PERIODS.some((p) => p.value === asked) ? asked : "month") as Period;
  const [from, to] = rangeOf(period, today, params.get("from"), params.get("to"));
  const f: Filters = {
    period, from, to, category: params.get("category") ?? "all", branch: params.get("branch") ?? "default", method: params.get("method") ?? "all",
  };
  const [sheet, setSheet] = useState(false);
  const [text, setText] = useState("");
  const dq = useSearch(text);

  // "default" follows the branch picked on Home; "all" or an id overrides it on this screen only.
  const branches = role.branches;
  const branch = f.branch === "default" ? homeBranch : f.branch === "all" ? null : Number(f.branch);
  const branchName = f.branch === "default" ? homeBranchName : branch ? branches.find((b) => b.id === branch)?.name ?? "" : "All branches";
  const branchOptions = [
    { value: "default", label: homeBranch ? homeBranchName : "All branches" },
    ...(homeBranch ? [{ value: "all", label: "All branches" }] : []),
    ...branches.filter((b) => b.id !== homeBranch).map((b) => ({ value: String(b.id), label: b.name })),
  ];

  const backwards = from > to;
  const filters = {
    from, to, ...(branch ? { branch } : {}), ...(dq ? { q: dq } : {}),
    ...(f.category !== "all" ? { category: f.category as ExpensesListCategory } : {}),
    ...(f.method !== "all" ? { method: f.method as ExpensesListMethod } : {}),
  };
  const list = useExpensesListInfinite(filters, { query: { ...paged, enabled: !backwards } });
  const totals = useGet<{ total_paise: number; by_category: Record<string, number> }>("/api/expenses/totals/", filters, !backwards);
  const { rows, count } = pages(list);
  const byCategory = Object.entries(totals.data?.by_category ?? {});
  const max = Math.max(1, ...byCategory.map(([, v]) => v));

  const go = (next: Partial<Filters>) => router.replace(listUrl({ ...f, ...next }), { scroll: false });
  const filtered = f.category !== "all" || f.branch !== "default" || f.method !== "all";
  const resetFilters = () => go({ category: "all", branch: "default", method: "all" });
  const narrowedBy = [f.category !== "all" && CATEGORIES[f.category], f.method !== "all" && `paid by ${METHODS[f.method]}`].filter(Boolean).join(", ");

  return (
    <div className="rl-app rl-root">
      <PageBar title="Expenses" sub={branchName} back="/more" action={<AddButton href="/expenses/new" label="Add Expense" />} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Paid to or note" label="Search who it was paid to, or the note" filter={{ on: filtered, onClick: () => setSheet(true) }} />
          <Chips name="ex-period" label="Period" value={period} onChange={(v) => go(v === "custom" ? { period: v, from, to } : { period: v })} options={PERIODS} />
        </div>
        {period === "custom" && (
          <div className="rl-pair" style={{ marginTop: "var(--space-4)" }}>
            <Field label="From" error={backwards ? "Pick a start date on or before the end date" : undefined}>{(id, desc) => (
              <input className="rl-field__input" id={id} type="date" value={from} aria-describedby={desc} aria-invalid={backwards}
                onChange={(e) => e.target.value && go({ from: e.target.value })} />
            )}</Field>
            <Field label="To">{(id) => (
              <input className="rl-field__input" id={id} type="date" value={to} onChange={(e) => e.target.value && go({ to: e.target.value })} />
            )}</Field>
          </div>
        )}
        {!backwards && (
          <>
            <Section label="Total">
              <Stat icon={Receipt} value={rupees(totals.data?.total_paise ?? 0)} label={`Spent ${rangeLabel(from, to)}`}
                note={`${plural(count, "expense")}${narrowedBy ? ` • ${narrowedBy}` : ""}`} />
            </Section>
            {f.category === "all" && (
              <Section title="By category">
                <ul className="rl-card rl-barlist" style={{ listStyle: "none", margin: 0, padding: "var(--space-3) var(--space-4)" }}>
                  {byCategory.map(([c, v]) => (
                    <li key={c} style={{ padding: "var(--space-1) 0" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}><span>{CATEGORIES[c] ?? c}</span><strong>{rupees(v)}</strong></div>
                      <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: v / max, background: "var(--ink)" }} /></span>
                    </li>
                  ))}
                  {!byCategory.length && <li className="rl-row__meta">Nothing spent in these dates.</li>}
                </ul>
              </Section>
            )}
            <section className="rl-section" aria-label="Expenses">
              <div className="rl-listmeta">
                <p role="status">{list.isLoading ? "Loading…" : `Showing ${plural(rows.length, "expense")}${rows.length < count ? ` of ${count}` : ""}`}</p>
                <p>Newest first</p>
              </div>
              {list.isLoading ? <SkeletonRows /> : rows.length ? (
                <><ul className="rl-card rl-mlist rl-mlist--compact">
                  {rows.map((e) => (
                    <li key={e.id}><div className="rl-mrow">
                      <span className="rl-chipicon" aria-hidden="true"><Icon as={Receipt} size="sm" /></span>
                      <span className="rl-row__title rl-mrow__name">{CATEGORIES[e.category]}{e.paid_to ? `, ${e.paid_to}` : ""}</span>
                      <span className="rl-row__meta rl-mrow__meta">{e.branch_name} • {e.spent_on ? day(e.spent_on) : ""} • {METHODS[e.method]}{e.note ? ` • ${e.note}` : ""}</span>
                      <span className="rl-mrow__time">{rupees(e.amount_paise)}</span>
                    </div></li>
                  ))}
                </ul>
                <LoadMore q={list} /></>
              ) : dq ? (
                <Empty icon={SearchX} title={`No expense matches “${dq}”`} text="Check the spelling, or try who it was paid to.">
                  <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setText("")}>Clear Search</button>
                </Empty>
              ) : filtered ? (
                <Empty icon={Receipt} title="No expenses match these filters" text="Try another category, branch or way of paying.">
                  <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={resetFilters}>Clear Filters</button>
                </Empty>
              ) : (
                <Empty icon={Receipt} title="No expenses in these dates" text="Add rent, salaries and bills to see what each branch costs.">
                  <Link className="rl-button rl-button--block" href="/expenses/new">Add Expense</Link>
                </Empty>
              )}
            </section>
          </>
        )}
      </main>
      <Sheet open={sheet} onClose={() => setSheet(false)} title="Filter expenses">
        <p className="rl-sheet__label" style={{ marginTop: 0, marginBottom: "var(--space-2)" }}>Category</p>
        <Chips name="ex-category" label="Filter by category" scroll={false} value={f.category} onChange={(v) => go({ category: v })}
          options={[{ value: "all", label: "All" }, ...Object.entries(CATEGORIES).map(([value, label]) => ({ value, label }))]} />
        {branches.length > 1 && (
          <>
            <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Branch</p>
            <Chips name="ex-branch" label="Filter by branch" scroll={false} value={f.branch} onChange={(v) => go({ branch: v })} options={branchOptions} />
          </>
        )}
        <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Paid by</p>
        <Chips name="ex-method" label="Filter by how it was paid" scroll={false} value={f.method} onChange={(v) => go({ method: v })}
          options={[{ value: "all", label: "Any way" }, ...Object.entries(METHODS).map(([value, label]) => ({ value, label }))]} />
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--block" type="button" onClick={() => setSheet(false)}>{list.isLoading ? "Done" : `Show ${plural(count, "expense")}`}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!filtered} onClick={resetFilters}>Reset</button>
        </div>
      </Sheet>
    </div>
  );
}

export default function Page() {
  return <Suspense><ExpensesPage /></Suspense>;
}
