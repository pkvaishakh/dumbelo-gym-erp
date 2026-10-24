"use client";
/* The diet plan form (New Plan, Copy and Edit) inside PlanFormShell: the day's targets, then the meals as entry cards:
 * a name, when and its calories side by side, and what's in it. */
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import type { DietPlan } from "@/api/gen/model";
import { ErrorText, Field, Icon } from "@/components/ui";
import { blankMeal, grams, mealHints, type MealRow, startingMeals, toMealRows, toMeals } from "@/lib/diets";

import { PlanFormShell } from "./plan-form";

type Targets = { kcal: string; protein_g: string; carbs_g: string; fat_g: string };
const text = (n?: number | null) => (n != null ? String(n) : "");

/** `plan` to edit, or `from` to start a copy of; neither for a new plan. */
export function DietForm({ plan, from }: { plan?: DietPlan; from?: DietPlan }) {
  const base = plan ?? from;
  const [t, setT] = useState<Targets>({ kcal: text(base?.kcal), protein_g: text(base?.protein_g), carbs_g: text(base?.carbs_g), fat_g: text(base?.fat_g) });
  const [meals, setMeals] = useState<MealRow[]>(() => (base ? toMealRows(base.meals) : startingMeals()));
  const [problems, setProblems] = useState<{ meals?: string; each: Record<number, string> }>({ each: {} });
  const setMeal = (i: number, m: MealRow) => setMeals(meals.map((x, j) => (j === i ? m : x)));

  function check() {
    const each: Record<number, string> = {};
    meals.forEach((m, i) => { if (m.food.trim() && !m.name.trim()) each[i] = "Name this meal, like Breakfast"; });
    const p = { each, meals: meals.some((m) => m.food.trim()) ? undefined : "Say what's in at least one meal" };
    setProblems(p);
    return !p.meals && !Object.keys(each).length;
  }
  const body = () => ({ kcal: grams(t.kcal), protein_g: grams(t.protein_g), carbs_g: grams(t.carbs_g), fat_g: grams(t.fat_g), meals: toMeals(meals) });

  return (
    <PlanFormShell kind="diet" plan={plan} from={from} check={check} body={body}>
      <fieldset className="rl-fieldset" style={{ gap: "var(--space-3)" }}>
        <legend>Each day <span className="rl-optional">(optional)</span></legend>
        <Field label="Calories a day, kcal">{(id) => (
          <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={500} max={6000} value={t.kcal} placeholder="1800" onChange={(e) => setT({ ...t, kcal: e.target.value })} />
        )}</Field>
        <div className="rl-minis">
          {(["protein_g", "carbs_g", "fat_g"] as const).map((k) => (
            <label className="rl-mini" key={k}><span>{{ protein_g: "Protein, g", carbs_g: "Carbs, g", fat_g: "Fat, g" }[k]}</span>
              <input type="number" inputMode="numeric" min={0} value={t[k]} placeholder="–" onChange={(e) => setT({ ...t, [k]: e.target.value })} /></label>
          ))}
        </div>
      </fieldset>
      <fieldset className={`rl-fieldset${problems.meals ? " is-invalid" : ""}`} style={{ gap: "var(--space-3)" }}>
        <legend>Meals</legend>
        <ol className="rl-entries">
          {meals.map((m, i) => (
            <li className="rl-card rl-entry" key={i}>
              <div className="rl-entry__head">
                <input className="rl-entry__name" value={m.name} maxLength={60} placeholder={`Meal ${i + 1}`} aria-label={`Meal ${i + 1} name`}
                  onChange={(e) => setMeal(i, { ...m, name: e.target.value })} />
                {meals.length > 1 && (
                  <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Remove ${m.name || `meal ${i + 1}`}`} onClick={() => setMeals(meals.filter((_, j) => j !== i))}>
                    <Icon as={Trash2} size="sm" />
                  </button>
                )}
              </div>
              <div className="rl-minis" style={{ gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
                <label className="rl-mini"><span>When</span><input value={m.time} maxLength={20} placeholder={mealHints(i).time} onChange={(e) => setMeal(i, { ...m, time: e.target.value })} /></label>
                <label className="rl-mini"><span>Calories</span><input type="number" inputMode="numeric" min={0} max={3000} value={m.kcal} placeholder="–" onChange={(e) => setMeal(i, { ...m, kcal: e.target.value })} /></label>
              </div>
              <Field label="What's in it" area error={problems.each[i]}>{(id) => (
                <textarea className="rl-field__input" id={id} rows={2} maxLength={300} value={m.food} placeholder={mealHints(i).food}
                  onChange={(e) => setMeal(i, { ...m, food: e.target.value })} />
              )}</Field>
            </li>
          ))}
        </ol>
        <ErrorText>{problems.meals}</ErrorText>
        {meals.length < 12 && (
          <button className="rl-button rl-button--soft rl-button--sm" type="button" style={{ justifySelf: "start" }} onClick={() => setMeals([...meals, blankMeal()])}>
            <Icon as={Plus} size="sm" />Add Meal
          </button>
        )}
      </fieldset>
    </PlanFormShell>
  );
}
