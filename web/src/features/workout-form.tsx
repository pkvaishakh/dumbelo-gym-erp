"use client";
/* The workout plan form (New Plan, Copy and Edit) inside PlanFormShell: days, each with the body parts it works and
 * its exercises as the design's ExerciseEntry rows: name, then sets, reps and load side by side. */
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import type { WorkoutPlan } from "@/api/gen/model";
import { ErrorText, Field, Icon } from "@/components/ui";
import { partChoices } from "@/lib/pt";
import { blankDay, blankExercise, type DayRow, toDays, toRows } from "@/lib/workouts";

import { PlanFormShell } from "./plan-form";

/** What's missing on each day before it can be saved, in the words shown under it. */
function problemsOf(days: DayRow[]) {
  const p: Record<number, string> = {};
  days.forEach((d, i) => {
    if (!d.title.trim()) p[i] = "Give this day a title, like Day 1 or Push day";
    else if (!d.exercises.some((e) => e.name.trim())) p[i] = "Add an exercise to this day";
  });
  return p;
}

/** `plan` to edit, or `from` to start a copy of; neither for a new plan. */
export function WorkoutForm({ plan, from }: { plan?: WorkoutPlan; from?: WorkoutPlan }) {
  const base = plan ?? from;
  const [days, setDays] = useState<DayRow[]>(() => (base ? toRows(base.days) : [blankDay(1)]));
  const [problems, setProblems] = useState<Record<number, string>>({});
  const check = () => { const p = problemsOf(days); setProblems(p); return !Object.keys(p).length; };
  return (
    <PlanFormShell kind="workout" plan={plan} from={from} check={check} body={() => ({ days: toDays(days) })}>
      {days.map((d, i) => (
        <DayFields key={i} n={i + 1} value={d} problem={problems[i]} onChange={(v) => setDays(days.map((x, j) => (j === i ? v : x)))}
          onRemove={days.length > 1 ? () => setDays(days.filter((_, j) => j !== i)) : undefined} />
      ))}
      {days.length < 14 && (
        <button className="rl-button rl-button--secondary" type="button" onClick={() => setDays([...days, blankDay(days.length + 1)])}>
          <Icon as={Plus} size="sm" />Add Day
        </button>
      )}
    </PlanFormShell>
  );
}

/** One day: its title, the body parts it works, and its exercises. */
function DayFields({ n, value: d, onChange, onRemove, problem }: { n: number; value: DayRow; onChange: (d: DayRow) => void; onRemove?: () => void; problem?: string }) {
  const parts = partChoices(d.body_parts);
  const setEx = (i: number, e: DayRow["exercises"][number]) => onChange({ ...d, exercises: d.exercises.map((x, j) => (j === i ? e : x)) });
  return (
    <fieldset className={`rl-fieldset${problem ? " is-invalid" : ""}`} style={{ gap: "var(--space-3)" }}>
      <legend style={{ display: "flex", width: "100%", alignItems: "center" }}>
        <span style={{ flex: 1 }}>Day {n}</span>
        {onRemove && <button className="rl-link rl-link--plain" type="button" onClick={onRemove}><span>Remove Day</span></button>}
      </legend>
      <Field label="Title">{(id) => (
        <input className="rl-field__input" id={id} value={d.title} maxLength={60} placeholder="Push day" onChange={(e) => onChange({ ...d, title: e.target.value })} />
      )}</Field>
      <p className="rl-field__label" style={{ margin: 0 }} aria-hidden="true">Works <span className="rl-optional">(optional)</span></p>
      <div className="rl-chips" role="group" aria-label={`Day ${n} works`}>
        {parts.map((p) => (
          <label className="rl-chipopt" key={p}>
            <input type="checkbox" checked={d.body_parts.includes(p)}
              onChange={(e) => onChange({ ...d, body_parts: e.target.checked ? [...d.body_parts, p] : d.body_parts.filter((x) => x !== p) })} />
            <span>{p}</span>
          </label>
        ))}
      </div>
      <ol className="rl-entries">
        {d.exercises.map((e, i) => (
          <li className="rl-card rl-entry" key={i}>
            <div className="rl-entry__head">
              <input className="rl-entry__name" value={e.name} maxLength={80} placeholder={`Exercise ${i + 1}`} aria-label={`Day ${n}, exercise ${i + 1}`}
                onChange={(ev) => setEx(i, { ...e, name: ev.target.value })} />
              {d.exercises.length > 1 && (
                <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Remove ${e.name || `exercise ${i + 1}`}`}
                  onClick={() => onChange({ ...d, exercises: d.exercises.filter((_, j) => j !== i) })}>
                  <Icon as={Trash2} size="sm" />
                </button>
              )}
            </div>
            <div className="rl-minis">
              <label className="rl-mini"><span>Sets</span><input type="number" inputMode="numeric" min={1} max={20} value={e.sets} onChange={(ev) => setEx(i, { ...e, sets: ev.target.value })} /></label>
              <label className="rl-mini"><span>Reps</span><input value={e.reps} maxLength={20} placeholder="8" onChange={(ev) => setEx(i, { ...e, reps: ev.target.value })} /></label>
              <label className="rl-mini"><span>Load</span><input value={e.load} maxLength={30} placeholder="None" onChange={(ev) => setEx(i, { ...e, load: ev.target.value })} /></label>
            </div>
          </li>
        ))}
      </ol>
      <ErrorText>{problem}</ErrorText>
      {d.exercises.length < 30 && (
        <button className="rl-button rl-button--soft rl-button--sm" type="button" style={{ justifySelf: "start" }}
          onClick={() => onChange({ ...d, exercises: [...d.exercises, blankExercise()] })}>
          <Icon as={Plus} size="sm" />Add Exercise
        </button>
      )}
    </fieldset>
  );
}
