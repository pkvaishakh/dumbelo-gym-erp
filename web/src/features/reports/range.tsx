"use client";
/* The one period and one branch a report answers to, kept in the URL so Back and a shared link keep them. */
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { BranchChip } from "@/components/shell";
import { Field, Seg } from "@/components/ui";
import type { ApiError } from "@/lib/api";
import { gymToday, rangeLabel } from "@/lib/format";
import { fieldError } from "@/lib/hooks";
import { isPeriod, PERIODS, rangeError, rangeOf, type Period } from "@/lib/reports";
import { useSession } from "@/lib/session";

type Change = { period?: Period; from?: string; to?: string; branch?: string };

/** The report's period, days and branch from the URL. `branch` is "all" or an id in the URL; without one, the admin's
 *  branch from the session. Days come from the gym's clock, never the device's. */
export function useReportRange() {
  const params = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const { role, branch: chosen, setBranch } = useSession();
  const today = gymToday(role.timezone);
  const asked = params.get("period");
  const period: Period = isPeriod(asked) ? asked : "7d";
  const [from, to] = rangeOf(period, today, params.get("from"), params.get("to"));
  const inUrl = params.get("branch");
  const branch = inUrl === "all" ? null : inUrl && /^\d+$/.test(inUrl) ? Number(inUrl) : chosen;
  const invalid = period === "custom" ? rangeError(from, to, today) : null;

  const query = new URLSearchParams();
  if (period !== "7d") query.set("period", period);
  if (period === "custom") { query.set("from", from); query.set("to", to); }
  if (inUrl) query.set("branch", inUrl);
  const search = query.toString();

  const go = (next: Change) => {
    const q = new URLSearchParams(search);
    if (next.period) {
      if (next.period === "7d") q.delete("period"); else q.set("period", next.period);
      if (next.period !== "custom") { q.delete("from"); q.delete("to"); }
    }
    if (next.from) q.set("from", next.from);
    if (next.to) q.set("to", next.to);
    if (next.branch) q.set("branch", next.branch);
    router.replace(q.toString() ? `${path}?${q}` : path, { scroll: false });
  };
  const pickBranch = (id: number | null) => { setBranch(id); go({ branch: id === null ? "all" : String(id) }); };

  return {
    today, period, from, to, branch, invalid, search, go, pickBranch,
    branchName: branch === null ? "All branches" : role.branches.find((b) => b.id === branch)?.name ?? "This branch",
    isAdmin: role.role === "admin",
    /** What the report endpoints take. */
    api: { from, to, ...(branch === null ? {} : { branch }) },
  };
}
export type ReportRange = ReturnType<typeof useReportRange>;

/** The period control, pinned above everything it changes, and the custom days when chosen. `meta` adds the days and
 *  the branch chip under it (category screens, whose app bar holds Download). */
export function ReportControls({ r, meta, error }: { r: ReportRange; meta?: boolean; error?: ApiError | null }) {
  const bar = useRef<HTMLDivElement>(null);
  // Five periods are wider than a small phone: keep the chosen one in view when the row scrolls.
  useEffect(() => { bar.current?.querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest", inline: "nearest" }); }, [r.period]);
  return (
    <>
      <div className="rl-searchbar rl-searchbar--period" ref={bar}>
        <Seg label="Period" value={r.period} options={PERIODS} onSurface
          onChange={(p) => r.go(p === "custom" ? { period: p, from: r.from, to: r.to } : { period: p })} />
      </div>
      {meta && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-3)", minWidth: 0 }}>
          <p className="rl-row__meta" style={{ margin: 0 }}>{rangeLabel(r.from, r.to)}{r.isAdmin ? "" : ` • ${r.branchName}`}</p>
          {r.isAdmin && <BranchChip value={r.branch} onPick={r.pickBranch} />}
        </div>
      )}
      {r.period === "custom" && <CustomRange key={`${r.from}~${r.to}`} r={r} error={error} />}
    </>
  );
}

/** Any days up to 3 months, ending today or earlier. Checked on Show Report with the API's words. */
function CustomRange({ r, error }: { r: ReportRange; error?: ApiError | null }) {
  const [from, setFrom] = useState(r.from);
  const [to, setTo] = useState(r.to);
  const [bad, setBad] = useState(r.invalid);
  const message = (f: "from" | "to") => (bad ? (bad.field === f ? bad.message : undefined) : fieldError(error ?? null, f));
  function show(e: React.FormEvent) {
    e.preventDefault();
    const wrong = rangeError(from, to, r.today);
    setBad(wrong);
    if (!wrong) r.go({ period: "custom", from, to });
  }
  const date = (label: "From" | "To", value: string, set: (v: string) => void) => (
    <Field label={label} error={message(label === "From" ? "from" : "to")}>{(id, desc) => (
      <input className="rl-field__input" id={id} type="date" max={r.today} value={value} aria-describedby={desc} aria-invalid={!!desc}
        onChange={(e) => { set(e.target.value); setBad(null); }} />
    )}</Field>
  );
  return (
    <form className="rl-form" noValidate onSubmit={show}>
      <div className="rl-pair">{date("From", from, setFrom)}{date("To", to, setTo)}</div>
      <button className="rl-button rl-button--block" type="submit">Show Report</button>
    </form>
  );
}
