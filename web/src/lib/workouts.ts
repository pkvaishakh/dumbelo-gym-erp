/** Workout plans: how an exercise reads, a plan in numbers, and the plan form's rows (typed as text) to and from
 *  the API's days. */
import type { Exercise, WorkoutDay, WorkoutDayRequest } from "@/api/gen/model";

import { plural } from "./format";

/** "4 sets × 8 reps", "3 sets × 30 sec", "15 min": plain numbers are reps, anything else reads as typed. */
export function exerciseLine(e: Exercise) {
  const reps = e.reps?.trim() ?? "";
  const r = /^\d+(\s*-\s*\d+)?$/.test(reps) ? `${reps.replace(/\s/g, "")} reps` : reps;
  if (e.sets && r) return `${plural(e.sets, "set")} × ${r}`;
  return e.sets ? plural(e.sets, "set") : r;
}

/** "3 days • 9 exercises". */
export function planSummary(days: readonly WorkoutDay[]) {
  return `${plural(days.length, "day")} • ${plural(days.reduce((n, d) => n + d.exercises.length, 0), "exercise")}`;
}

export type ExerciseRow = { name: string; sets: string; reps: string; load: string };
export type DayRow = { title: string; body_parts: string[]; exercises: ExerciseRow[] };

export const blankExercise = (): ExerciseRow => ({ name: "", sets: "3", reps: "", load: "" });
export const blankDay = (n: number): DayRow => ({ title: `Day ${n}`, body_parts: [], exercises: [blankExercise()] });

/** A plan's days as the form edits them. */
export function toRows(days: readonly WorkoutDay[]): DayRow[] {
  return days.map((d) => ({
    title: d.title, body_parts: [...(d.body_parts ?? [])],
    exercises: d.exercises.map((e) => ({ name: e.name, sets: e.sets ? String(e.sets) : "", reps: e.reps ?? "", load: e.load ?? "" })),
  }));
}

/** The form's days as the API takes them. Exercise rows left without a name are dropped, so a blank row at the end
 *  doesn't stop the save. */
export function toDays(rows: readonly DayRow[]): WorkoutDayRequest[] {
  return rows.map((d) => ({
    title: d.title.trim(), body_parts: d.body_parts,
    exercises: d.exercises.filter((e) => e.name.trim()).map((e) => ({
      name: e.name.trim(), sets: Number.parseInt(e.sets, 10) || null, reps: e.reps.trim(), load: e.load.trim(),
    })),
  }));
}
