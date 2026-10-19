"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { NewGym } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { TimeZoneField } from "@/features/console/parts";
import { ActionBar } from "@/features/sell";
import { SLUG_RULE, slugify } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

const BLANK = {
  name: "", slug: "", timezone: "Asia/Kolkata", branch: "", owner_email: "", owner_name: "", owner_password: "", billing_email: "",
};

/** New Gym: the gym, its first branch and its owner. It starts on trial; the owner can sign in at once. */
export default function NewGymPage() {
  const router = useRouter();
  const [f, setF] = useState(BLANK);
  const [slugTouched, setSlugTouched] = useState(false);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [made, setMade] = useState<NewGym | null>(null);
  const a = useAction();
  const set = (k: keyof typeof BLANK) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setF((old) => ({ ...old, [k]: v, ...(k === "name" && !slugTouched ? { slug: slugify(v) } : {}) }));
  };
  const err = (k: string) => errs[k] ?? fieldError(a.error, k);

  async function save() {
    const e: Record<string, string> = {};
    if (!f.name.trim()) e.name = "Enter the gym's name";
    if (!SLUG_RULE.test(f.slug)) e.slug = "Use 3 to 40 lowercase letters, numbers and dashes, like iron-house";
    if (!f.branch.trim()) e.branch = "Name the first branch";
    if (!/^\S+@\S+\.\S+$/.test(f.owner_email.trim())) e.owner_email = "Enter the owner's email";
    if (f.owner_password && f.owner_password.length < 8) e.owner_password = "Use at least 8 characters";
    setErrs(e);
    if (Object.keys(e).length) return;
    try {
      const out = await a.run<NewGym>("/api/platform/gyms/", { ...f, owner_email: f.owner_email.trim() }, { refresh: ["/api/platform/gyms/"] });
      setMade(out!);
    } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="New Gym" />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Gym name" error={err("name")}>
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={f.name} placeholder="Iron House" autoCapitalize="words" enterKeyHint="next" onChange={set("name")} />}
          </Field>
          <Field label="Short name" error={err("slug")} hint="The app uses it to find the gym. Lowercase letters, numbers and dashes. It can't change later.">
            {(id, d) => (
              <input className="rl-field__input" id={id} aria-describedby={d} value={f.slug} placeholder="iron-house" autoCapitalize="none" autoCorrect="off" spellCheck={false}
                enterKeyHint="next" onChange={(e) => { setSlugTouched(true); setF({ ...f, slug: e.target.value.toLowerCase() }); }} />
            )}
          </Field>
          <TimeZoneField value={f.timezone} onChange={(timezone) => setF({ ...f, timezone })} error={err("timezone")} />
          <Field label="First branch" error={err("branch")} hint="Its admin adds the opening hours and more branches.">
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={f.branch} placeholder="Indiranagar" autoCapitalize="words" enterKeyHint="next" onChange={set("branch")} />}
          </Field>
          <fieldset className="rl-fieldset"><legend>Owner</legend>
            <div className="rl-form">
              <Field label="Owner's email" error={err("owner_email")} hint="They sign in with it and look after the gym's Dumbelo plan.">
                {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="email" inputMode="email" autoComplete="off" autoCapitalize="none" value={f.owner_email} placeholder="owner@gym.in" onChange={set("owner_email")} />}
              </Field>
              <Field label="Owner's name" error={err("owner_name")} hint="Leave it empty if they already sign in to Dumbelo at another gym.">
                {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={f.owner_name} autoComplete="off" autoCapitalize="words" onChange={set("owner_name")} />}
              </Field>
              <Field label="First password" error={err("owner_password")} hint="For someone new to Dumbelo: tell them, and they change it from More. Leave it empty if they already sign in.">
                {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="text" autoComplete="new-password" autoCapitalize="none" spellCheck={false} value={f.owner_password} onChange={set("owner_password")} />}
              </Field>
              <Field label="Billing email" optional error={err("billing_email")} hint="Where Dumbelo's invoices go. The owner's email if you leave it empty.">
                {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="email" inputMode="email" autoComplete="off" autoCapitalize="none" value={f.billing_email} onChange={set("billing_email")} />}
              </Field>
            </div>
          </fieldset>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label="Create Gym" busy={a.busy} busyLabel="Creating…" onClick={save} />
      <Sheet open={!!made} onClose={() => router.push("/console/gyms")} closable={false}>
        {made && (
          <>
            <Confirm title={`${made.name} is ready`} text={made.owner_new_login
              ? `${made.owner_name} signs in with ${made.owner_email} and the first password you set. The gym is on trial until you activate it.`
              : `${made.owner_name} already signs in to Dumbelo, so they'll find ${made.name} with their other gyms. It's on trial until you activate it.`} />
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="button" onClick={() => router.push(`/console/gyms/${made.id}`)}>Open Gym</button>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => router.push("/console/gyms")}>Done</button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}
