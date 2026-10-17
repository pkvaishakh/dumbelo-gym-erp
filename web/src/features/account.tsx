"use client";
/* The signed-in person's own account: their details and their password. */
import { useState } from "react";

import { ErrorText, Field, Sheet } from "@/components/ui";
import { tokens } from "@/lib/api";
import { phone } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

export function AccountSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { me } = useSession();
  const fresh = () => ({ name: me.name, email: me.email ?? "", phone: me.phone ? phone(me.phone) : "" });
  const [f, setF] = useState(fresh);
  const [was, setWas] = useState(false);
  if (open !== was) { // start from what's saved each time the sheet opens
    setWas(open);
    if (open) setF(fresh());
  }
  const a = useAction();
  async function save() {
    try { await a.run("/api/me/", { name: f.name.trim(), email: f.email.trim(), phone: f.phone.trim() || null }, { method: "PATCH", refresh: ["/api/me/"] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Edit Details">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Name" error={fieldError(a.error, "name")}>{(id) => <input className="rl-field__input" id={id} autoComplete="name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
        <Field label="Email" hint="You sign in with this email." error={fieldError(a.error, "email")}>
          {(id) => <input className="rl-field__input" id={id} type="email" autoComplete="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />}
        </Field>
        <Field label="Mobile number" optional error={fieldError(a.error, "phone")}>
          {(id) => <input className="rl-field__input" id={id} type="tel" inputMode="numeric" autoComplete="tel" value={f.phone} placeholder="98765 43210" onChange={(e) => setF({ ...f, phone: e.target.value })} />}
        </Field>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
      </form>
    </Sheet>
  );
}

export function PasswordSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const blank = { current: "", next: "", again: "" };
  const [f, setF] = useState(blank);
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState(false);
  const a = useAction();
  const close = () => { setF(blank); setErr(undefined); setDone(false); a.clearError(); onClose(); };
  async function save() {
    if (f.next.length < 8) return setErr("Use at least 8 characters");
    if (f.next !== f.again) return setErr("The two new passwords don't match");
    try {
      const out = await a.run<{ access: string; refresh: string }>("/api/me/password/", { current_password: f.current, new_password: f.next }, { refresh: [] });
      if (out) tokens.set(out.access, out.refresh); // this device stays signed in; every other one is signed out
      setDone(true);
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={done ? undefined : "Change Password"}>
      {done ? (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">Password changed</h2><p className="rl-confirm__text">Use it next time you sign in. Any other phone or computer signed in as you has been signed out.</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Current password" error={a.error?.code === "wrong_password" ? a.error.message : undefined}>
            {(id) => <input className="rl-field__input" id={id} type="password" autoComplete="current-password" value={f.current} onChange={(e) => setF({ ...f, current: e.target.value })} />}
          </Field>
          <Field label="New password" hint="At least 8 characters." error={err ?? fieldError(a.error, "new_password")}>
            {(id) => <input className="rl-field__input" id={id} type="password" autoComplete="new-password" value={f.next} onChange={(e) => { setF({ ...f, next: e.target.value }); setErr(undefined); }} />}
          </Field>
          <Field label="New password again">
            {(id) => <input className="rl-field__input" id={id} type="password" autoComplete="new-password" value={f.again} onChange={(e) => { setF({ ...f, again: e.target.value }); setErr(undefined); }} />}
          </Field>
          <ErrorText>{a.error && !a.error.fields && a.error.code !== "wrong_password" ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Change Password"}</button></div>
        </form>
      )}
    </Sheet>
  );
}
