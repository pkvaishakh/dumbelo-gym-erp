"use client";
/* What's in a workout plan: its days, each the design's ExerciseList. The rest of a plan's screens are shared with
 * diet plans (coach-plans, coach-screens). */
import { Check } from "lucide-react";

import type { WorkoutDay } from "@/api/gen/model";
import { Icon, Section } from "@/components/ui";
import { partsLabel } from "@/lib/pt";
import { exerciseLine } from "@/lib/workouts";

/** A plan's days, each a numbered list of its exercises. */
export function PlanDays({ days }: { days: readonly WorkoutDay[] }) {
  return (
    <>
      {days.map((d, i) => (
        <Section key={i} title={d.title} aside={d.body_parts?.length ? <p className="rl-section__aside">{partsLabel(d.body_parts)}</p> : undefined}>
          <ul className="rl-card rl-exlist">
            {d.exercises.map((e, j) => (
              <li key={j}><div className="rl-ex">
                <span className="rl-ex__num"><span>{j + 1}</span><Icon as={Check} size="xs" /></span>
                <span className="rl-ex__text"><span className="rl-row__title">{e.name}</span>{exerciseLine(e) && <span className="rl-row__meta">{exerciseLine(e)}</span>}</span>
                {e.load && <span className="rl-ex__load">{e.load}</span>}
              </div></li>
            ))}
          </ul>
        </Section>
      ))}
    </>
  );
}
