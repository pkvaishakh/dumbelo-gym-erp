"use client";
/* What's in a diet plan: the day's targets, then its meals as the design's MealList. The trainer sets the plan; there's
 * no ticking meals eaten yet, so each meal leads with its icon instead of the tick. */
import { UtensilsCrossed } from "lucide-react";

import type { Meal } from "@/api/gen/model";
import { Icon, Section } from "@/components/ui";
import { kcalLabel, macrosLine } from "@/lib/diets";

type Targets = { kcal?: number | null; protein_g?: number | null; carbs_g?: number | null; fat_g?: number | null };

/** The day's calories as the figure, with the macros under it. Nothing when the plan sets no targets. */
export function DietTargets({ of }: { of: Targets }) {
  const macros = macrosLine(of);
  if (!of.kcal && !macros) return null;
  return (
    <Section title="Each day">
      <div className="rl-card rl-card--pad">
        {of.kcal ? <p className="rl-figure" style={{ margin: 0 }}>{of.kcal.toLocaleString("en-IN")} <small>kcal a day</small></p> : null}
        {macros && <p className="rl-row__meta" style={{ margin: of.kcal ? "var(--space-1) 0 0" : 0 }}>{macros}</p>}
      </div>
    </Section>
  );
}

/** The day's meals in order: name, when, what's in it, and its calories. */
export function Meals({ meals }: { meals: readonly Meal[] }) {
  return (
    <Section title="Meals">
      <ul className="rl-card rl-meals">
        {meals.map((m, i) => (
          <li className="rl-meal" key={i}>
            <span className="rl-chipicon" aria-hidden="true" style={{ justifySelf: "center" }}><Icon as={UtensilsCrossed} size="sm" /></span>
            <div className="rl-meal__text">
              <p className="rl-meal__head"><span className="rl-row__title">{m.name}</span></p>
              {m.time && <p className="rl-row__meta" style={{ margin: 0 }}>{m.time}</p>}
              <p className="rl-row__body">{m.food}</p>
            </div>
            {m.kcal != null ? <p className="rl-meal__kcal">{m.kcal.toLocaleString("en-IN")}<small>kcal</small></p> : <span />}
          </li>
        ))}
      </ul>
      {meals.some((m) => m.kcal != null) && <p className="rl-row__meta" style={{ marginTop: "var(--space-2)" }}>
        Meals add up to {kcalLabel(meals.reduce((t, m) => t + (m.kcal ?? 0), 0))}.
      </p>}
    </Section>
  );
}
