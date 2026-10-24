"use client";
/* Coaching plans, workout and diet alike: which kind is which (KINDS), reading either kind's plans and who's on them,
 * the plan's card on a member's profile, giving a plan to a member from either side (a plan for this member, or a
 * member for this plan), and the member's own plans on their Home. What's inside a plan is drawn by PlanBody.
 * Each data hook calls both kinds' generated hooks and switches the other off: the generated hooks are overloaded,
 * so one can't be picked into a variable and called. */
import { ClipboardList, Dumbbell, Eye, Salad, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useDietAssignmentsList } from "@/api/gen/diet-assignments/diet-assignments";
import { useDietPlansList, useDietPlansListInfinite, useDietPlansRetrieve } from "@/api/gen/diet-plans/diet-plans";
import { useMembersList } from "@/api/gen/members/members";
import type { DietAssignment, DietPlan, WorkoutAssignment, WorkoutAssignmentsListParams, WorkoutPlan, WorkoutPlansListParams } from "@/api/gen/model";
import { useWorkoutAssignmentsList } from "@/api/gen/workout-assignments/workout-assignments";
import { useWorkoutPlansList, useWorkoutPlansListInfinite, useWorkoutPlansRetrieve } from "@/api/gen/workout-plans/workout-plans";
import { Choices, ErrorText, Field, Icon, MenuRow, Photo, SearchField, Section, Sheet, SkeletonRows, Status } from "@/components/ui";
import { dietSummary } from "@/lib/diets";
import { day } from "@/lib/format";
import { paged, pages, useAction, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import { planSummary } from "@/lib/workouts";

import { DietTargets, Meals } from "./diets";
import { PlanDays } from "./workouts";

export type Kind = "workout" | "diet";
export type AnyPlan = WorkoutPlan | DietPlan;
export type AnyGiven = WorkoutAssignment | DietAssignment;

/** Each kind's words, addresses and icon. `route` is the gym's library, `own` the member's page. */
export const KINDS: Record<Kind, { one: string; many: string; route: string; own: string; api: string; given: string; icon: LucideIcon; empty: string }> = {
  workout: { one: "Workout plan", many: "Workout plans", route: "/workouts", own: "/workout", api: "/api/workout-plans/", given: "/api/workout-assignments/", icon: Dumbbell,
    empty: "Your trainer gives you one. Ask them next time you're at the gym." },
  diet: { one: "Diet plan", many: "Diet plans", route: "/diets", own: "/diet", api: "/api/diet-plans/", given: "/api/diet-assignments/", icon: Salad,
    empty: "Your trainer writes one for you. Ask them next time you're at the gym." },
};

/** What giving or ending a plan changes: who's on what, and each plan's count of members. */
const refreshFor = (k: Kind) => [KINDS[k].given, KINDS[k].api];

/** Trainers and admins write plans and give them; the desk and members only read. */
export function useCoach() {
  const { role } = useSession();
  return role.role === "admin" || role.role === "trainer";
}

/** "3 days • 9 exercises", or "5 meals • 1,800 kcal a day". */
export const planSummaryOf = (p: AnyPlan | AnyGiven) => ("days" in p ? planSummary(p.days) : dietSummary(p));
/** "3 days • 9 exercises • by Neha". */
export const planMeta = (p: AnyPlan) => `${planSummaryOf(p)} • by ${p.created_by_name}`;
/** "From Neha on 24 Oct 2026 • 3 days • 9 exercises". */
export const givenLine = (a: AnyGiven) => `From ${a.assigned_by_name} on ${day(a.assigned_at.slice(0, 10))} • ${planSummaryOf(a)}`;

/** What's in a plan: a workout's days, or a diet's targets and meals. */
export function PlanBody({ of }: { of: AnyPlan | AnyGiven }) {
  return "days" in of ? <PlanDays days={of.days} /> : <><DietTargets of={of} /><Meals meals={of.meals} /></>;
}

// ---- reading either kind ----

export function usePlans(kind: Kind, params: WorkoutPlansListParams, enabled = true) {
  const w = useWorkoutPlansList(params, { query: { enabled: enabled && kind === "workout" } });
  const d = useDietPlansList(params, { query: { enabled: enabled && kind === "diet" } });
  const rows: AnyPlan[] = (kind === "workout" ? w.data?.data.results : d.data?.data.results) ?? [];
  return { rows, isLoading: kind === "workout" ? w.isLoading : d.isLoading };
}

export function usePlansInfinite(kind: Kind, params: WorkoutPlansListParams) {
  const w = useWorkoutPlansListInfinite(params, { query: { ...paged, enabled: kind === "workout" } });
  const d = useDietPlansListInfinite(params, { query: { ...paged, enabled: kind === "diet" } });
  const { rows, count }: { rows: AnyPlan[]; count: number } = kind === "workout" ? pages(w) : pages(d);
  return { q: kind === "workout" ? w : d, rows, count };
}

export function usePlan(kind: Kind, id: number, enabled = true) {
  const w = useWorkoutPlansRetrieve(id, { query: { enabled: enabled && kind === "workout" } });
  const d = useDietPlansRetrieve(id, { query: { enabled: enabled && kind === "diet" } });
  const plan: AnyPlan | undefined = kind === "workout" ? w.data?.data : d.data?.data;
  return { plan, isError: kind === "workout" ? w.isError : d.isError };
}

export function useGiven(kind: Kind, params: WorkoutAssignmentsListParams, enabled = true) {
  const w = useWorkoutAssignmentsList(params, { query: { enabled: enabled && kind === "workout" } });
  const d = useDietAssignmentsList(params, { query: { enabled: enabled && kind === "diet" } });
  const rows: AnyGiven[] = (kind === "workout" ? w.data?.data.results : d.data?.data.results) ?? [];
  return { rows, isLoading: kind === "workout" ? w.isLoading : d.isLoading };
}

// ---- on a member's profile, and on their Home ----

/** The member's plan of this kind on their profile. Trainers and admins give one or change it; the eye opens it. */
export function PlanCard({ kind, member, name }: { kind: Kind; member: number; name: string }) {
  const k = KINDS[kind];
  const coach = useCoach();
  const given = useGiven(kind, { member, current: true, limit: 1 });
  const a = given.rows[0];
  const [assigning, setAssigning] = useState(false);
  if (given.isLoading) return <Section title={k.one}><SkeletonRows n={1} /></Section>;
  if (!a && !coach) return null;
  return (
    <Section title={k.one}>
      <div className="rl-card rl-card--pad">
        {a ? (
          <>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-2)" }}>
              <span style={{ flex: 1, minWidth: 0 }}>
                <span className="rl-row__title" style={{ display: "block" }}>{a.plan_name}</span>
                <span className="rl-row__meta" style={{ display: "block" }}>{givenLine(a)}</span>
              </span>
              <Link className="rl-iconbtn rl-iconbtn--plain" href={`${k.route}/${a.plan}`} aria-label={`View ${a.plan_name}`} title="View Plan"
                style={{ margin: "-10px -8px 0 0", background: "none" }}>
                <Icon as={Eye} size="sm" />
              </Link>
            </div>
            {a.note && <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>“{a.note}”</p>}
          </>
        ) : <p className="rl-row__meta" style={{ margin: 0 }}>No {k.one.toLowerCase()} yet.</p>}
        {coach && (
          <div className="rl-pass-actions" style={{ marginTop: "var(--space-3)" }}>
            <button className="rl-button rl-button--soft rl-button--sm" type="button" aria-haspopup="dialog" onClick={() => setAssigning(true)}>
              <Icon as={ClipboardList} size="sm" />{a ? "Change Plan" : "Assign Plan"}
            </button>
          </div>
        )}
      </div>
      <AssignPlanSheet kind={kind} open={assigning} member={member} name={name} current={a?.plan} onClose={() => setAssigning(false)} />
    </Section>
  );
}

/** The member's own plans on their Home: a row to each, once their trainer has given them one. */
export function MyPlansRows() {
  const workout = useGiven("workout", { current: true, limit: 1 }).rows[0];
  const diet = useGiven("diet", { current: true, limit: 1 }).rows[0];
  if (!workout && !diet) return null;
  return (
    <Section title="Your plans">
      <ul className="rl-card rl-remind">
        {workout && <MenuRow icon={KINDS.workout.icon} title={workout.plan_name} value={planSummaryOf(workout)} href={KINDS.workout.own} />}
        {diet && <MenuRow icon={KINDS.diet.icon} title={diet.plan_name} value={planSummaryOf(diet)} href={KINDS.diet.own} />}
      </ul>
    </Section>
  );
}

// ---- giving a plan to a member ----

/** Pick a plan for this member, with an optional note for them. The plan of this kind they're on now ends. */
function AssignPlanSheet({ kind, open, member, name, current, onClose }: { kind: Kind; open: boolean; member: number; name: string; current?: number; onClose: () => void }) {
  const [text, setText] = useState("");
  const q = useSearch(text);
  const plans = usePlans(kind, { limit: 20, ...(q ? { q } : {}) }, open);
  const [plan, setPlan] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const a = useAction();
  const close = () => { setText(""); setPlan(null); setNote(""); a.clearError(); onClose(); };
  async function go() {
    try { await a.run(KINDS[kind].given, { plan, member, note: note.trim() }, { refresh: refreshFor(kind) }); close(); } catch { /* shown */ }
  }
  const rows = plans.rows.filter((p) => p.id !== current);
  return (
    <Sheet open={open} onClose={close} title={current ? "Change Plan" : "Assign Plan"}>
      <p className="rl-row__meta">For {name}.{current ? " The plan they're on now ends." : ""}</p>
      <SearchField value={text} onChange={setText} placeholder="Plan name or goal" label="Find a plan" />
      {plans.isLoading ? <SkeletonRows n={2} /> : rows.length
        ? <Choices name={`assign-${kind}`} value={plan} onChange={setPlan} options={rows.map((p) => ({ value: p.id, title: p.name, meta: planMeta(p) }))} />
        : <p className="rl-row__meta">{q ? `No plan matches “${q}”.` : `No other plans yet. Write one in More, ${KINDS[kind].many}.`}</p>}
      <NoteField value={note} onChange={setNote} />
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy || plan === null} onClick={go}>{a.busy ? "Saving…" : "Assign Plan"}</button>
      </div>
    </Sheet>
  );
}

/** Pick a member for this plan: a trainer finds only their own members. */
export function AssignMemberSheet({ kind, open, plan, onClose }: { kind: Kind; open: boolean; plan: AnyPlan; onClose: () => void }) {
  const [text, setText] = useState("");
  const q = useSearch(text);
  const { branch } = useSession();
  const found = useMembersList({ q, limit: 8, ...(branch ? { branch } : {}) }, { query: { enabled: open && q.length >= 2 } });
  const [who, setWho] = useState<{ id: number; name: string } | null>(null);
  const [note, setNote] = useState("");
  const a = useAction();
  const close = () => { setText(""); setWho(null); setNote(""); a.clearError(); onClose(); };
  async function go() {
    try { await a.run(KINDS[kind].given, { plan: plan.id, member: who!.id, note: note.trim() }, { refresh: refreshFor(kind) }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Assign to Member">
      {who ? (
        <>
          <div className="rl-sheet__who"><Photo name={who.name} /><span><span className="rl-row__title">{who.name}</span><span className="rl-row__meta">Gets {plan.name}. The plan they&apos;re on now ends.</span></span></div>
          <NoteField value={note} onChange={setNote} />
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Saving…" : "Assign Plan"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setWho(null); a.clearError(); }}>Pick Someone Else</button>
          </div>
        </>
      ) : (
        <>
          <SearchField value={text} onChange={setText} placeholder="Name, phone or member ID" label="Find the member" autoFocus />
          {q.length >= 2 && (
            <ul className="rl-card rl-results" style={{ marginTop: "var(--space-3)" }}>
              {(found.data?.data.results ?? []).map((m) => (
                <li key={m.id}><button className="rl-result" type="button" style={{ width: "100%", textAlign: "left", background: "none", border: 0, font: "inherit" }} onClick={() => setWho(m)}>
                  <Photo name={m.name} />
                  <span className="rl-result__text"><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code}</span></span>
                  <Status status={m.status} />
                </button></li>
              ))}
              {found.data && !found.data.data.results.length && <li style={{ padding: "var(--space-4)" }}><p className="rl-row__meta" style={{ margin: 0 }}>No member of yours matches “{q}”.</p></li>}
            </ul>
          )}
        </>
      )}
    </Sheet>
  );
}

function NoteField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Field label="Note for them" optional>{(id) => (
      <input className="rl-field__input" id={id} value={value} maxLength={300} placeholder="Start light this week" onChange={(e) => onChange(e.target.value)} />
    )}</Field>
  );
}
