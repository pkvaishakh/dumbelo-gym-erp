"use client";
/* The task screen around either plan form (New Plan, Copy and Edit): its name and goal, saving, and where saving goes.
 * Each kind's form puts its own fields inside and says whether they're ready (`check`) and what they send (`body`). */
import { useRouter } from "next/navigation";
import { useState } from "react";

import { TaskBar } from "@/components/shell";
import { ErrorText, Field } from "@/components/ui";
import { ActionBar } from "@/features/sell";
import { useAction } from "@/lib/hooks";

import { type AnyPlan, KINDS, type Kind } from "./coach-plans";

export function PlanFormShell({ kind, plan, from, check, body, children }: {
  kind: Kind; plan?: AnyPlan; from?: AnyPlan; check: () => boolean; body: () => object; children: React.ReactNode;
}) {
  const k = KINDS[kind];
  const router = useRouter();
  const [name, setName] = useState(plan ? plan.name : from ? `${from.name} (copy)` : "");
  const [goal, setGoal] = useState((plan ?? from)?.goal ?? "");
  const [nameError, setNameError] = useState<string>();
  const a = useAction();

  async function save() {
    const named = !!name.trim();
    setNameError(named ? undefined : "Give the plan a name");
    if (!check() || !named) return;
    try {
      const out = await a.run<AnyPlan>(plan ? `${k.api}${plan.id}/` : k.api, { name: name.trim(), goal: goal.trim(), ...body() },
        { method: plan ? "PATCH" : "POST", refresh: [k.api, k.given] });
      if (out) router.replace(`${k.route}/${out.id}`);
    } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={plan ? "Edit Plan" : from ? "Copy Plan" : "New Plan"} aside={k.one} />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Name" error={nameError}>{(id) => (
            <input className="rl-field__input" id={id} value={name} maxLength={120} placeholder={kind === "workout" ? "Beginner full body" : "Lean veg 1,800"}
              onChange={(e) => { setName(e.target.value); setNameError(undefined); }} />
          )}</Field>
          <Field label="Goal" optional hint="Who it's for, so other trainers pick the right plan.">{(id) => (
            <input className="rl-field__input" id={id} value={goal} maxLength={160} placeholder={kind === "workout" ? "Fat loss, 3 days a week" : "Fat loss, vegetarian"}
              onChange={(e) => setGoal(e.target.value)} />
          )}</Field>
          {children}
          <ErrorText>{a.error?.message}</ErrorText>
        </form>
      </main>
      <ActionBar label={plan ? "Save Changes" : "Save Plan"} onClick={save} busy={a.busy} />
    </div>
  );
}
