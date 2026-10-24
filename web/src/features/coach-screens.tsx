"use client";
/* The screens of coaching plans, workout and diet alike: the gym's library (every trainer's plans, Mine and Archived
 * in the address so Back keeps them), one plan (Assign to Member, Copy, Edit, Archive), New Plan with
 * ?copy=, Edit Plan, and the member's own plan. Routes are thin: /workouts/… and /diets/… pass their kind. */
import { Archive, ArchiveRestore, ClipboardList, Copy, Pencil, UserPlus } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { PageBar } from "@/components/shell";
import { AddButton, Chips, Empty, ErrorText, Icon, LoadMore, SearchField, Section, SkeletonRows } from "@/components/ui";
import { plural } from "@/lib/format";
import { useAction, useSearch } from "@/lib/hooks";

import { type AnyPlan, AssignMemberSheet, givenLine, KINDS, type Kind, PlanBody, planMeta, planSummaryOf, useCoach, useGiven, usePlan, usePlansInfinite } from "./coach-plans";
import { DietForm } from "./diet-form";
import { WorkoutForm } from "./workout-form";

type Show = "all" | "mine" | "archived";

/** The gym's plans of this kind. Wrap the route in Suspense: the filter lives in the address. */
export function PlanLibrary({ kind }: { kind: Kind }) {
  const k = KINDS[kind];
  const params = useSearchParams();
  const router = useRouter();
  const coach = useCoach();
  const show: Show = (["mine", "archived"] as const).find((s) => s === params.get("show")) ?? "all";
  const [text, setText] = useState("");
  const q = useSearch(text);
  const { q: list, rows, count } = usePlansInfinite(kind, {
    ...(q ? { q } : {}), ...(show === "mine" ? { mine: true } : {}), ...(show === "archived" ? { archived: true } : {}),
  });
  const options: { value: Show; label: string }[] = [{ value: "all", label: "All" }, ...(coach ? [{ value: "mine" as const, label: "Mine" }] : []), { value: "archived", label: "Archived" }];

  return (
    <div className="rl-app rl-root">
      <PageBar title={k.many} sub={list.isLoading ? " " : plural(count, "plan")} back="/more"
        action={coach ? <AddButton href={`${k.route}/new`} label="New Plan" /> : undefined} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder="Plan name or goal" label="Search plans" />
          <Chips name={`${kind}-show`} label="Show" value={show} options={options}
            onChange={(v) => router.replace(v === "all" ? k.route : `${k.route}?show=${v}`, { scroll: false })} />
        </div>
        <section className="rl-section">
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((p) => (
                  <li key={p.id}><Link className="rl-mrow" href={`${k.route}/${p.id}`}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={k.icon} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{p.name}</span>
                    <span className="rl-row__meta rl-mrow__meta">{planMeta(p)}</span>
                    {p.members_count > 0 && <span className="rl-mrow__time rl-mrow__time--muted">{plural(p.members_count, "member")}</span>}
                  </Link></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : q ? (
            <Empty icon={ClipboardList} title="No plans match" text={`Nothing called “${q}”. Try another word.`} />
          ) : (
            <Empty icon={ClipboardList} title={show === "archived" ? "Nothing archived" : show === "mine" ? "You haven't written a plan yet" : `No ${k.many.toLowerCase()} yet`}
              text={show === "archived" ? "Plans you archive wait here, ready to restore." : "Write a plan once, then give it to any of your members."}>
              {coach && show !== "archived" && <Link className="rl-button" href={`${k.route}/new`}>New Plan</Link>}
            </Empty>
          )}
        </section>
      </main>
    </div>
  );
}

/** One plan: what it's for, and what's in it. */
export function PlanScreen({ kind }: { kind: Kind }) {
  const k = KINDS[kind];
  const pid = Number(useParams<{ id: string }>().id);
  const coach = useCoach();
  const { plan: p, isError } = usePlan(kind, pid);
  const [assigning, setAssigning] = useState(false);
  const a = useAction();
  const archive = () => a.run(`${k.api}${pid}/`, { is_active: !p!.is_active }, { method: "PATCH", refresh: [k.api] }).catch(() => {});

  if (isError) return <Shell title={k.one}><Empty icon={ClipboardList} title="Plan not found" text="It may be from another gym, or the link is wrong." /></Shell>;
  if (!p) return <Shell title={k.one}><SkeletonRows /></Shell>;
  return (
    <Shell title={p.name} sub={`${k.one} by ${p.created_by_name}`}>
      <Section label="Plan">
        <div className="rl-card rl-card--pad">
          {p.goal && <p className="rl-row__title" style={{ margin: 0 }}>{p.goal}</p>}
          <p className="rl-row__meta" style={{ margin: p.goal ? "var(--space-1) 0 0" : 0 }}>
            {planSummaryOf(p)} • {p.members_count ? `${plural(p.members_count, "member")} on it` : "No one on it yet"}
            {!p.is_active && " • Archived"}
          </p>
          {coach && p.is_active && (
            <button className="rl-button rl-button--block" type="button" aria-haspopup="dialog" style={{ marginTop: "var(--space-3)" }} onClick={() => setAssigning(true)}>
              <Icon as={UserPlus} size="sm" />Assign to Member
            </button>
          )}
          {coach && (
            <div className="rl-pass-actions" style={{ marginTop: "var(--space-2)" }}>
              <Link className="rl-button rl-button--soft rl-button--sm" href={`${k.route}/new?copy=${p.id}`}><Icon as={Copy} size="sm" />Copy</Link>
              {p.can_change && <Link className="rl-button rl-button--soft rl-button--sm" href={`${k.route}/${p.id}/edit`}><Icon as={Pencil} size="sm" />Edit</Link>}
              {p.can_change && (
                <button className="rl-button rl-button--secondary rl-button--sm" type="button" disabled={a.busy} onClick={archive}>
                  <Icon as={p.is_active ? Archive : ArchiveRestore} size="sm" />{p.is_active ? "Archive" : "Restore"}
                </button>
              )}
            </div>
          )}
          <ErrorText>{a.error?.message}</ErrorText>
        </div>
      </Section>
      <PlanBody of={p} />
      {coach && <AssignMemberSheet kind={kind} open={assigning} plan={p} onClose={() => setAssigning(false)} />}
    </Shell>
  );
}

/** New Plan, or with ?copy=<id> a copy of another trainer's plan to make your own. Wrap the route in Suspense. */
export function NewPlanScreen({ kind }: { kind: Kind }) {
  const copy = Number(useSearchParams().get("copy")) || 0;
  const { plan: from } = usePlan(kind, copy, !!copy);
  if (copy && !from) return <TaskLoading />;
  return <PlanForm kind={kind} from={from} />;
}

/** Edit Plan: its author's or an admin's (the API refuses anyone else). */
export function EditPlanScreen({ kind }: { kind: Kind }) {
  const { plan } = usePlan(kind, Number(useParams<{ id: string }>().id));
  return plan ? <PlanForm kind={kind} plan={plan} /> : <TaskLoading />;
}

/** Each kind's own form, given the plan to edit or copy narrowed to that kind. */
function PlanForm({ kind, plan, from }: { kind: Kind; plan?: AnyPlan; from?: AnyPlan }) {
  const workout = (p?: AnyPlan) => (p && "days" in p ? p : undefined);
  const diet = (p?: AnyPlan) => (p && "meals" in p ? p : undefined);
  return kind === "workout" ? <WorkoutForm plan={workout(plan)} from={workout(from)} /> : <DietForm plan={diet(plan)} from={diet(from)} />;
}

/** The member's own plan of this kind, as their trainer gave it: who from, their note, and what's in it. */
export function MyPlanScreen({ kind }: { kind: Kind }) {
  const k = KINDS[kind];
  const given = useGiven(kind, { current: true, limit: 1 });
  const a = given.rows[0];
  return (
    <div className="rl-app rl-root">
      <PageBar title={k.one} sub={a?.plan_name} back />
      <main className="rl-app__main">
        {given.isLoading ? <SkeletonRows /> : !a ? (
          <Empty icon={k.icon} title={`No ${k.one.toLowerCase()} yet`} text={k.empty} />
        ) : (
          <>
            <Section label="Plan">
              <div className="rl-card rl-card--pad">
                {a.goal && <p className="rl-row__title" style={{ margin: 0 }}>{a.goal}</p>}
                <p className="rl-row__meta" style={{ margin: a.goal ? "var(--space-1) 0 0" : 0 }}>{givenLine(a)}</p>
                {a.note && <p className="rl-statusline" style={{ marginTop: "var(--space-3)" }}>“{a.note}”</p>}
              </div>
            </Section>
            <PlanBody of={a} />
          </>
        )}
      </main>
    </div>
  );
}

function Shell({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) {
  return (
    <div className="rl-app rl-root">
      <PageBar title={title} sub={sub} back />
      <main className="rl-app__main">{children}</main>
    </div>
  );
}

function TaskLoading() {
  return <div className="rl-app rl-app--task rl-root"><main className="rl-app__main"><SkeletonRows /></main></div>;
}
