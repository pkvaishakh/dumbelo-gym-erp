import { describe, expect, it } from "vitest";

import { blankDay, exerciseLine, planSummary, toDays, toRows } from "./workouts";

describe("workout plans", () => {
  it("reads an exercise as sets and reps, or as typed", () => {
    expect(exerciseLine({ name: "Bench Press", sets: 4, reps: "8" })).toBe("4 sets × 8 reps");
    expect(exerciseLine({ name: "Lunge", sets: 3, reps: "10 - 12" })).toBe("3 sets × 10-12 reps");
    expect(exerciseLine({ name: "Plank", sets: 3, reps: "45 sec" })).toBe("3 sets × 45 sec");
    expect(exerciseLine({ name: "Cycling", sets: null, reps: "20 min" })).toBe("20 min");
    expect(exerciseLine({ name: "Stretch", sets: 1 })).toBe("1 set");
  });
  it("counts a plan's days and exercises", () => {
    expect(planSummary([{ title: "A", exercises: [{ name: "x" }, { name: "y" }] }, { title: "B", exercises: [{ name: "z" }] }])).toBe("2 days • 3 exercises");
  });
  it("turns the form's rows into days, dropping exercises left without a name", () => {
    const rows = blankDay(1);
    rows.exercises = [{ name: " Squat ", sets: "4", reps: " 8 ", load: "60 kg" }, { name: " ", sets: "3", reps: "", load: "" }, { name: "Walk", sets: "", reps: "10 min", load: "" }];
    expect(toDays([rows])).toEqual([{ title: "Day 1", body_parts: [], exercises: [
      { name: "Squat", sets: 4, reps: "8", load: "60 kg" }, { name: "Walk", sets: null, reps: "10 min", load: "" },
    ] }]);
    expect(toRows(toDays([rows]))[0].exercises[1]).toEqual({ name: "Walk", sets: "", reps: "10 min", load: "" });
  });
});
