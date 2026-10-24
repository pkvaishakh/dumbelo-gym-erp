"use client";
/* The members list's order and its filters beyond status: membership plan, workout plan, diet plan and branch. The
 * sheet starts with the order as chips (newest first by default), then shows one row per filter with what's chosen; tapping a row opens its options in the sheet, with a search once a list is long,
 * so a gym with many plans still gets a short sheet. What's on also shows above the list as pills that take it off. */
import { ArrowLeft, Building2, Check, Tag, X, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { Chips, Icon, MenuRow, SearchField, Sheet, SkeletonRows } from "@/components/ui";
import { plural } from "@/lib/format";
import { useSearch } from "@/lib/hooks";

import { KINDS, type Kind, planSummaryOf, usePlan, usePlans } from "./coach-plans";

export type MemberSort = "newest" | "name";
export type MemberFilters = { status: string; plan: string; branch: string; workout: string; diet: string; sort: MemberSort };
/** The list's orders, newest first by default; `meta` says it above the list. */
export const SORTS: { value: MemberSort; label: string; meta: string }[] = [
  { value: "newest", label: "Newest", meta: "Newest first" }, { value: "name", label: "Name", meta: "Sorted by name" },
];
export const DEFAULT_SORT: MemberSort = "newest";
/** The order from the address, newest first when it's missing or not one the list offers. */
export const sortOf = (asked: string | null): MemberSort => SORTS.find((s) => s.value === asked)?.value ?? DEFAULT_SORT;
/** The filters the sheet sets, each at "show everyone". Status has its own chips on the list. */
export const SHEET_DEFAULTS = { plan: "all", branch: "default", workout: "all", diet: "all" } as const;
type SheetKey = keyof typeof SHEET_DEFAULTS;
export type Option = { value: string; label: string; meta?: string };

/** Lists longer than this get a search in the sheet. */
const LONG = 7;

/** A workout or diet filter in words: "Any", "On a plan", "No plan" or the plan's name. */
function useCoachLabel(kind: Kind, value: string) {
  const id = Number(value) || 0;
  const { plan } = usePlan(kind, id, !!id);
  return value === "all" ? "Any" : value === "any" ? "On a plan" : value === "none" ? "No plan" : plan?.name ?? "…";
}

export function MemberFilterSheet({ open, onClose, f, set, plans, branches, count, loading }: {
  open: boolean; onClose: () => void; f: MemberFilters; set: (next: Partial<MemberFilters>) => void;
  plans: Option[]; branches: Option[]; count: number; loading: boolean;
}) {
  const [picking, setPicking] = useState<SheetKey | null>(null);
  const workout = useCoachLabel("workout", f.workout);
  const diet = useCoachLabel("diet", f.diet);
  const close = () => { setPicking(null); onClose(); };
  const pick = (key: SheetKey) => (value: string) => { set({ [key]: value }); setPicking(null); };
  const changed = f.sort !== DEFAULT_SORT || (Object.keys(SHEET_DEFAULTS) as SheetKey[]).some((k) => f[k] !== SHEET_DEFAULTS[k]);
  const labelOf = (options: Option[], value: string) => options.find((o) => o.value === value)?.label ?? "…";
  const titles: Record<SheetKey, string> = { plan: "Membership plan", workout: KINDS.workout.one, diet: KINDS.diet.one, branch: "Branch" };

  return (
    <Sheet open={open} onClose={close} title={picking ? titles[picking] : "Sort and filter"}>
      {picking ? (
        <>
          <button className="rl-link rl-link--plain" type="button" style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)", background: "none", border: 0, padding: 0 }}
            onClick={() => setPicking(null)}>
            <Icon as={ArrowLeft} size="xs" /><span>All filters</span>
          </button>
          {picking === "workout" || picking === "diet"
            ? <CoachOptions kind={picking} value={f[picking]} onPick={pick(picking)} />
            : <Options options={picking === "plan" ? plans : branches} value={f[picking]} onPick={pick(picking)} icon={picking === "plan" ? Tag : Building2} />}
        </>
      ) : (
        <>
          <p className="rl-sheet__label">Sort by</p>
          <Chips name="ml-sort" label="Sort by" scroll={false} value={f.sort} onChange={(v) => set({ sort: v })} options={SORTS}
            style={{ marginTop: "var(--space-2)", marginBottom: "var(--space-4)" }} />
          <p className="rl-sheet__label">Filter</p>
          <ul className="rl-card rl-remind" style={{ marginTop: "var(--space-2)" }}>
            <MenuRow icon={Tag} title={titles.plan} value={labelOf(plans, f.plan)} onClick={() => setPicking("plan")} />
            <MenuRow icon={KINDS.workout.icon} title={titles.workout} value={workout} onClick={() => setPicking("workout")} />
            <MenuRow icon={KINDS.diet.icon} title={titles.diet} value={diet} onClick={() => setPicking("diet")} />
            {branches.length > 1 && <MenuRow icon={Building2} title={titles.branch} value={labelOf(branches, f.branch)} onClick={() => setPicking("branch")} />}
          </ul>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" onClick={close}>{loading ? "Done" : `Show ${plural(count, "member")}`}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!changed} onClick={() => set({ ...SHEET_DEFAULTS, sort: DEFAULT_SORT })}>Reset</button>
          </div>
        </>
      )}
    </Sheet>
  );
}

/** A fixed list (membership plans, branches), searched by name on the phone once it's long. */
function Options({ options, value, onPick, icon }: { options: Option[]; value: string; onPick: (v: string) => void; icon: LucideIcon }) {
  const [text, setText] = useState("");
  const q = text.trim().toLowerCase();
  const shown = q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;
  return (
    <>
      {options.length > LONG && <div style={{ marginTop: "var(--space-3)" }}><SearchField value={text} onChange={setText} placeholder="Search" label="Search the options" /></div>}
      <OptionList options={shown} value={value} onPick={onPick} icon={icon} empty={`Nothing matches “${text.trim()}”.`} />
    </>
  );
}

/** A workout or diet filter: anyone, on a plan, on none, or one plan, the plans searched on the server. */
function CoachOptions({ kind, value, onPick }: { kind: Kind; value: string; onPick: (v: string) => void }) {
  const [text, setText] = useState("");
  const q = useSearch(text);
  const plans = usePlans(kind, { limit: 50, ...(q ? { q } : {}) });
  const fixed: Option[] = [
    { value: "all", label: "Any", meta: "Everyone, on a plan or not" },
    { value: "any", label: "On a plan", meta: `Has a ${KINDS[kind].one.toLowerCase()}` },
    { value: "none", label: "No plan", meta: `Needs a ${KINDS[kind].one.toLowerCase()}` },
  ];
  return (
    <>
      {!q && <OptionList options={fixed} value={value} onPick={onPick} icon={KINDS[kind].icon} />}
      <p className="rl-sheet__label">On this plan</p>
      <div style={{ marginTop: "var(--space-2)" }}><SearchField value={text} onChange={setText} placeholder="Plan name or goal" label="Find a plan" /></div>
      {plans.isLoading ? <div style={{ marginTop: "var(--space-2)" }}><SkeletonRows n={2} /></div> : (
        <OptionList options={plans.rows.map((p) => ({ value: String(p.id), label: p.name, meta: planSummaryOf(p) }))} value={value} onPick={onPick}
          icon={KINDS[kind].icon} empty={q ? `No plan matches “${q}”.` : "No plans written yet."} />
      )}
    </>
  );
}

function OptionList({ options, value, onPick, icon, empty }: { options: Option[]; value: string; onPick: (v: string) => void; icon: LucideIcon; empty?: string }) {
  if (!options.length) return <p className="rl-row__meta">{empty}</p>;
  return (
    <ul className="rl-sheet__list">
      {options.map((o) => (
        <li key={o.value}><button className="rl-sheet__item" type="button" aria-pressed={o.value === value} onClick={() => onPick(o.value)}>
          <span className="rl-chipicon" aria-hidden="true"><Icon as={icon} size="sm" /></span>
          <span className="rl-sheet__text"><span className="rl-row__title" style={{ display: "block" }}>{o.label}</span>{o.meta && <span className="rl-row__meta" style={{ display: "block" }}>{o.meta}</span>}</span>
          {o.value === value && <Icon as={Check} size="sm" />}
        </button></li>
      ))}
    </ul>
  );
}

/** What the sheet has on, as pills above the list; tapping one takes that filter off. */
export function ActiveFilters({ f, set, plans, branches }: { f: MemberFilters; set: (next: Partial<MemberFilters>) => void; plans: Option[]; branches: Option[] }) {
  const workout = useCoachLabel("workout", f.workout);
  const diet = useCoachLabel("diet", f.diet);
  const on: { key: SheetKey; label: string }[] = [];
  if (f.plan !== "all") on.push({ key: "plan", label: plans.find((o) => o.value === f.plan)?.label ?? "Plan" });
  if (f.workout !== "all") on.push({ key: "workout", label: `Workout: ${workout}` });
  if (f.diet !== "all") on.push({ key: "diet", label: `Diet: ${diet}` });
  if (f.branch !== "default") on.push({ key: "branch", label: branches.find((o) => o.value === f.branch)?.label ?? "Branch" });
  if (!on.length) return null;
  return (
    <div className="rl-chips" style={{ marginBottom: "var(--space-2)" }} aria-label="Filters on">
      {on.map((x) => (
        <button key={x.key} className="rl-chip" type="button" aria-label={`Remove filter ${x.label}`} onClick={() => set({ [x.key]: SHEET_DEFAULTS[x.key] })}>
          {x.label}<Icon as={X} size="xs" />
        </button>
      ))}
    </div>
  );
}
