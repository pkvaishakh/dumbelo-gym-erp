"use client";
import { useState } from "react";

import type { Staff } from "@/api/gen/model";
import { ErrorText, Field } from "@/components/ui";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

import { ActionBar } from "./sell";
import { cleanUsername, ExistingLoginField, type LoginKind, LoginKindChips, UsernameField } from "./username";

const DAYS = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Add Trainer / Add Receptionist, and Edit… with the same fields in the same order. Adding someone who already
 *  signs in to Dumbelo (at another gym) takes only their username: their name, details and password stay theirs. */
export function StaffForm({ roleName, staff, onSaved }: {
  roleName: "trainer" | "receptionist"; staff?: Staff;
  /** `linked`: they brought the login they already had, so they sign in with their own password. */
  onSaved: (s: Staff, linked: boolean) => void;
}) {
  const { role } = useSession();
  const [kind, setKind] = useState<LoginKind>("new");
  const [f, setF] = useState({
    name: staff?.name ?? "", username: staff?.username ?? "", existing_username: "", email: staff?.email ?? "", phone: staff?.phone?.replace(/^\+91/, "") ?? "", password: "",
    branches: staff?.branches ?? (role.branches[0] ? [role.branches[0].id] : []), shift: staff?.shift ?? "", specialities: staff?.specialities ?? "",
    day_off: staff?.day_off ?? "", device_user_id: staff?.device_user_id ?? "",
  });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const a = useAction();
  const linking = !staff && kind === "existing";
  async function save() {
    const e: Record<string, string> = {};
    if (linking) {
      if (!cleanUsername(f.existing_username)) e.existing_username = "Enter the username they sign in with";
    } else {
      if (!f.name.trim()) e.name = "Enter their full name";
      if (f.email && !/^\S+@\S+\.\S+$/.test(f.email)) e.email = "Enter an email like name@gym.com, or leave it empty";
      if (!staff && f.password.length < 8) e.password = "Use at least 8 characters";
      if (staff && !cleanUsername(f.username)) e.username = "Enter their username";
    }
    if (!f.branches.length) e.branches = "Choose at least one branch";
    setErrs(e);
    if (Object.keys(e).length) return;
    const { existing_username, name, username, email, phone, password, ...work } = f;
    const login = linking ? { existing_username: cleanUsername(existing_username) }
      : { name, username: cleanUsername(username) || undefined, email: email || null, phone: phone || null, ...(staff ? {} : { password }) };
    try {
      const s = await a.run<Staff>(staff ? `/api/staff/${staff.id}/` : "/api/staff/", { ...work, ...login, role: roleName }, { method: staff ? "PATCH" : "POST", refresh: ["/api/staff/"] });
      onSaved(s!, linking);
    } catch { /* shown */ }
  }
  const set = (k: keyof typeof f) => (ev: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: ev.target.value });
  const err = (k: string) => errs[k] || fieldError(a.error, k);
  return (
    <>
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        {!staff && <LoginKindChips value={kind} onChange={setKind} />}
        {linking ? (
          <ExistingLoginField value={f.existing_username} onChange={(v) => setF({ ...f, existing_username: v })} error={err("existing_username")} />
        ) : (
          <>
            <Field label="Full name" error={err("name")}>{(id) => <input className="rl-field__input" id={id} value={f.name} autoCapitalize="words" onChange={set("name")} />}</Field>
            <Field label="Email" optional error={err("email")}>{(id) => <input className="rl-field__input" id={id} type="email" inputMode="email" autoCapitalize="none" value={f.email ?? ""} onChange={set("email")} />}</Field>
            <UsernameField value={f.username} onChange={(v) => setF({ ...f, username: v })} email={f.email ?? ""} name={f.name} error={err("username")}
              current={staff?.username} optional={!staff} />
            <Field label="Mobile number" optional prefix="+91" error={err("phone")}>{(id) => <input className="rl-field__input" id={id} type="tel" inputMode="numeric" value={f.phone} onChange={set("phone")} />}</Field>
            {!staff && <Field label="First password" error={err("password")} hint="Share it with them in person.">{(id) => <input className="rl-field__input" id={id} type="text" autoComplete="new-password" value={f.password} onChange={set("password")} />}</Field>}
          </>
        )}
        <fieldset className="rl-fieldset"><legend>Branches</legend>
          <div className="rl-chips">
            {role.branches.map((b) => (
              <label className="rl-chipopt" key={b.id}>
                <input type="checkbox" checked={f.branches.includes(b.id)} onChange={(e) => setF({ ...f, branches: e.target.checked ? [...f.branches, b.id] : f.branches.filter((x) => x !== b.id) })} />
                <span>{b.name}</span>
              </label>
            ))}
          </div>
          <ErrorText>{err("branches")}</ErrorText>
        </fieldset>
        <Field label="Shift" optional>{(id) => <input className="rl-field__input" id={id} value={f.shift} placeholder="Morning" onChange={set("shift")} />}</Field>
        {roleName === "trainer" && <Field label="Specialities" optional>{(id) => <input className="rl-field__input" id={id} value={f.specialities} placeholder="Strength, mobility" onChange={set("specialities")} />}</Field>}
        <Field label="Day off" optional>{(id) => (
          <select className="rl-field__input" id={id} value={f.day_off} onChange={set("day_off")}>{DAYS.map((d) => <option key={d} value={d}>{d || "Not set"}</option>)}</select>
        )}</Field>
        <Field label="Turnstile number" optional hint="Their number on the biometric or turnstile, so their punches count as check-ins.">{(id) => <input className="rl-field__input" id={id} inputMode="numeric" value={f.device_user_id} onChange={set("device_user_id")} />}</Field>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      </form>
      <ActionBar label={staff ? "Save Changes" : `Add ${roleName === "trainer" ? "Trainer" : "Receptionist"}`} onClick={save} busy={a.busy} />
    </>
  );
}
