/** Diet plans: a plan in numbers, its targets in words, and the plan form's rows (typed as text) to and from the
 *  API's meals. */
import type { Meal, MealRequest } from "@/api/gen/model";

import { plural } from "./format";

type Targets = { kcal?: number | null; protein_g?: number | null; carbs_g?: number | null; fat_g?: number | null };

/** "1,800 kcal" */
export const kcalLabel = (n: number) => `${n.toLocaleString("en-IN")} kcal`;

/** "5 meals • 1,800 kcal a day" */
export function dietSummary(p: Targets & { meals: readonly Meal[] }) {
  return [plural(p.meals.length, "meal"), p.kcal ? `${kcalLabel(p.kcal)} a day` : ""].filter(Boolean).join(" • ");
}

/** "Protein 110 g • Carbs 200 g • Fat 55 g", leaving out any target not set. */
export function macrosLine(p: Targets) {
  return ([["Protein", p.protein_g], ["Carbs", p.carbs_g], ["Fat", p.fat_g]] as const)
    .filter(([, g]) => g != null).map(([name, g]) => `${name} ${g} g`).join(" • ");
}

export type MealRow = { name: string; time: string; food: string; kcal: string };

export const blankMeal = (name = ""): MealRow => ({ name, time: "", food: "", kcal: "" });

/** A new plan's meals, each with the hints its empty fields show: when, and what might be in it. */
const STARTING = [
  ["Breakfast", "7:30 AM", "Oats with banana and milk"], ["Lunch", "1:30 PM", "2 rotis, dal, grilled chicken or paneer, salad"],
  ["Evening snack", "5 PM", "Sprouts chaat and green tea"], ["Dinner", "8:30 PM", "Brown rice, dal, vegetables"],
] as const;
export const startingMeals = () => STARTING.map(([name]) => blankMeal(name));
/** The hints for the meal in place `i`, or plain ones past the starting four. */
export const mealHints = (i: number) => {
  const [, time, food] = STARTING[i] ?? ["", "When", "What they eat"];
  return { time, food };
};

export function toMealRows(meals: readonly Meal[]): MealRow[] {
  return meals.map((m) => ({ name: m.name, time: m.time ?? "", food: m.food, kcal: m.kcal != null ? String(m.kcal) : "" }));
}

/** The form's meals as the API takes them. A meal left with nothing in it is dropped, so a spare row doesn't stop the
 *  save. */
export function toMeals(rows: readonly MealRow[]): MealRequest[] {
  return rows.filter((m) => m.food.trim()).map((m) => ({
    name: m.name.trim(), time: m.time.trim(), food: m.food.trim(), kcal: m.kcal.trim() ? Number.parseInt(m.kcal, 10) : null,
  }));
}

/** A whole number typed in a target field, or null when it's left empty. */
export const grams = (v: string) => (v.trim() ? Number.parseInt(v, 10) : null);
