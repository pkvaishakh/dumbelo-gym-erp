"use client";
import { parseISO, startOfMonth, subDays } from "date-fns";
import { SearchX, Wallet } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { PaymentsListMethod } from "@/api/gen/model";
import { usePaymentsListInfinite } from "@/api/gen/payments/payments";
import { PageBar } from "@/components/shell";
import { Chips, Empty, Field, LoadMore, Photo, SearchField, Section, Sheet, SkeletonRows, Stat } from "@/components/ui";
import { isoDate, plural, rangeLabel, rupees, until } from "@/lib/format";
import { paged, pages, useGet, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Collection } from "@/lib/types";

const METHOD = { upi: "UPI", cash: "Cash", card: "Card", bank: "Bank transfer" } as Record<string, string>;

type Period = "today" | "yesterday" | "7d" | "month" | "custom";
const PERIODS: { value: Period; label: string }[] = [
  { value: "today", label: "Today" }, { value: "yesterday", label: "Yesterday" }, { value: "7d", label: "7 days" },
  { value: "month", label: "This month" }, { value: "custom", label: "Custom" },
];

/** The first and last day a period covers. Receptionists see one day at a time, so they only get "custom" with one day. */
function rangeOf(period: Period, today: string, from: string | null, to: string | null): [string, string] {
  const t = parseISO(today);
  if (period === "yesterday") { const y = isoDate(subDays(t, 1)); return [y, y]; }
  if (period === "7d") return [isoDate(subDays(t, 6)), today];
  if (period === "month") return [isoDate(startOfMonth(t)), today];
  if (period === "custom") return [from || today, to || from || today];
  return [today, today];
}

type Filters = { period: Period; from: string; to: string; branch: string; method: string };

/** Filters live in the address, so Back and a shared link keep the list as it was. */
function listUrl(f: Filters) {
  const p = new URLSearchParams();
  if (f.period !== "today") p.set("period", f.period);
  if (f.period === "custom") { p.set("from", f.from); p.set("to", f.to); }
  if (f.branch !== "default") p.set("branch", f.branch);
  if (f.method !== "all") p.set("method", f.method);
  const s = p.toString();
  return s ? `/collection?${s}` : "/collection";
}

function CollectionPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role, branch: homeBranch, branchName: homeBranchName } = useSession();
  const isAdmin = role.role === "admin";
  const today = isoDate(new Date());
  const asked = params.get("period");
  const period = (PERIODS.some((p) => p.value === asked) && (isAdmin || asked === "custom") ? asked : "today") as Period;
  const [from, to] = rangeOf(period, today, params.get("from"), isAdmin ? params.get("to") : params.get("from"));
  const f: Filters = { period, from, to, branch: params.get("branch") ?? "default", method: params.get("method") ?? "all" };
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
    ...(f.method !== "all" ? { method: f.method as PaymentsListMethod } : {}),
  };
  const col = useGet<Collection>("/api/payments/collection/", filters, !backwards);
  const list = usePaymentsListInfinite({ ...filters, voided: false }, { query: { ...paged, enabled: !backwards } });
  const { rows, count } = pages(list);

  const go = (next: Partial<Filters>) => router.replace(listUrl({ ...f, ...next }), { scroll: false });
  const filtered = f.branch !== "default" || f.method !== "all";
  const resetFilters = () => go({ branch: "default", method: "all" });
  const oneDay = from === to;
  const when = from === today && oneDay ? "today" : oneDay ? `on ${rangeLabel(from, to)}` : rangeLabel(from, to);

  return (
    <div className="rl-app rl-root">
      <PageBar title="Collection" sub={branchName} back="/more" />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Member, ID, phone or note" label="Search payments by member name, member ID, phone or note"
            filter={{ on: filtered, onClick: () => setSheet(true) }} />
          {isAdmin && <Chips name="col-period" label="Period" value={period} onChange={(v) => go(v === "custom" ? { period: v, from, to } : { period: v })} options={PERIODS} />}
        </div>
        {isAdmin ? period === "custom" && (
          <div className="rl-pair" style={{ marginTop: "var(--space-4)" }}>
            <Field label="From" error={backwards ? "Pick a start date on or before the end date" : undefined}>{(id, desc) => (
              <input className="rl-field__input" id={id} type="date" max={today} value={from} aria-describedby={desc} aria-invalid={backwards}
                onChange={(e) => e.target.value && go({ from: e.target.value })} />
            )}</Field>
            <Field label="To">{(id) => (
              <input className="rl-field__input" id={id} type="date" max={today} value={to} onChange={(e) => e.target.value && go({ to: e.target.value })} />
            )}</Field>
          </div>
        ) : (
          <div style={{ marginTop: "var(--space-4)" }}>
            <Field label="Day">{(id) => (
              <input className="rl-field__input" id={id} type="date" max={today} value={from}
                onChange={(e) => e.target.value && go(e.target.value === today ? { period: "today" } : { period: "custom", from: e.target.value, to: e.target.value })} />
            )}</Field>
          </div>
        )}
        {!backwards && (
          <>
            <Section label="Totals">
              <div className="rl-kpis rl-kpis--pair">
                <Stat icon={Wallet} value={col.data ? rupees(col.data.total_paise) : "–"} label={`Collected ${when}`} note={col.data ? plural(col.data.count, "payment") : undefined} />
                <Stat icon={Wallet} value={col.data ? rupees(col.data.by_method.cash ?? 0) : "–"} label="In cash" note={oneDay ? "To hand over" : undefined} />
              </div>
              {col.data && f.method === "all" && (
                <ul className="rl-card rl-barlist" style={{ marginTop: "var(--space-3)", padding: "var(--space-3) var(--space-4)", listStyle: "none" }}>
                  {Object.entries(col.data.by_method).map(([m, v]) => (
                    <li key={m} style={{ display: "flex", justifyContent: "space-between", padding: "var(--space-1) 0" }}><span>{METHOD[m] ?? m}</span><strong>{rupees(v)}</strong></li>
                  ))}
                </ul>
              )}
            </Section>
            <Section title="Payments">
              <div className="rl-listmeta">
                <p role="status">{list.isLoading ? "Loading…" : `Showing ${plural(rows.length, "payment")}${rows.length < count ? ` of ${count}` : ""}`}</p>
                <p>Newest first</p>
              </div>
              {list.isLoading ? <SkeletonRows /> : rows.length ? (
                <><ul className="rl-card rl-mlist rl-mlist--compact">
                  {rows.map((p) => (
                    <li key={p.id}><Link className="rl-mrow" href={`/members/${p.member}`}>
                      <Photo name={p.member_name} />
                      <span className="rl-row__title rl-mrow__name">{p.member_name}</span>
                      <span className="rl-row__meta rl-mrow__meta">{METHOD[p.method]} • {p.taken_by_name}{p.taken_at ? ` • ${until(p.taken_at)}` : ""}</span>
                      <span className="rl-mrow__time">{rupees(p.amount_paise)}</span>
                    </Link></li>
                  ))}
                </ul>
                <LoadMore q={list} /></>
              ) : dq ? (
                <Empty icon={SearchX} title={`No payment matches “${dq}”`} text="Check the spelling, or try the member's phone number.">
                  <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setText("")}>Clear Search</button>
                </Empty>
              ) : filtered ? (
                <Empty icon={Wallet} title="No payments match these filters" text="Try another branch or way of paying.">
                  <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={resetFilters}>Clear Filters</button>
                </Empty>
              ) : <Empty icon={Wallet} title={oneDay ? "No payments this day" : "No payments in these dates"} text="Payments taken at the desk show up here." />}
            </Section>
          </>
        )}
      </main>
      <Sheet open={sheet} onClose={() => setSheet(false)} title="Filter payments">
        <p className="rl-sheet__label" style={{ marginTop: 0, marginBottom: "var(--space-2)" }}>Paid by</p>
        <Chips name="col-method" label="Filter by how it was paid" scroll={false} value={f.method} onChange={(v) => go({ method: v })}
          options={[{ value: "all", label: "Any way" }, ...Object.entries(METHOD).map(([value, label]) => ({ value, label }))]} />
        {branches.length > 1 && (
          <>
            <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Branch</p>
            <Chips name="col-branch" label="Filter by branch" scroll={false} value={f.branch} onChange={(v) => go({ branch: v })} options={branchOptions} />
          </>
        )}
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--block" type="button" onClick={() => setSheet(false)}>{list.isLoading ? "Done" : `Show ${plural(count, "payment")}`}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!filtered} onClick={resetFilters}>Reset</button>
        </div>
      </Sheet>
    </div>
  );
}

export default function Page() {
  return <Suspense><CollectionPage /></Suspense>;
}
