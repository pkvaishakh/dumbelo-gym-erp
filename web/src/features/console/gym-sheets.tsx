"use client";
/* A gym's own changes in the Console: its details, and suspending or activating it. */
import { useState } from "react";

import type { GymDetail } from "@/api/gen/model";
import { ErrorText, Field, Sheet } from "@/components/ui";
import { fieldError, useAction } from "@/lib/hooks";

import { TimeZoneField } from "./parts";

const GYMS = "/api/platform/gyms/";

export function EditGymSheet({ gym, open, onClose }: { gym: GymDetail; open: boolean; onClose: () => void }) {
  const fresh = () => ({ name: gym.name, timezone: gym.timezone, billing_email: gym.billing_email });
  const [f, setF] = useState(fresh);
  const [was, setWas] = useState(false);
  if (open !== was) { // start from what's saved each time the sheet opens
    setWas(open);
    if (open) setF(fresh());
  }
  const a = useAction();
  async function save() {
    try { await a.run(`${GYMS}${gym.id}/`, { ...f, name: f.name.trim(), billing_email: f.billing_email.trim() }, { method: "PATCH", refresh: [GYMS] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Edit Gym">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Gym name" error={fieldError(a.error, "name")}>
          {(id) => <input className="rl-field__input" id={id} autoCapitalize="words" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}
        </Field>
        <TimeZoneField value={f.timezone} onChange={(timezone) => setF({ ...f, timezone })} error={fieldError(a.error, "timezone")} />
        <Field label="Billing email" optional hint="Where Dumbelo's invoices go." error={fieldError(a.error, "billing_email")}>
          {(id) => <input className="rl-field__input" id={id} type="email" inputMode="email" autoCapitalize="none" value={f.billing_email} onChange={(e) => setF({ ...f, billing_email: e.target.value })} />}
        </Field>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
      </form>
    </Sheet>
  );
}

const STATUS_COPY = {
  suspend: {
    title: (name: string) => `Suspend ${name}?`,
    text: "Its staff and members can't use the app from their next tap, and the gym sends no messages. Its admins can still sign in to see their Dumbelo plan.",
    button: "Suspend Gym", busy: "Suspending…", keep: "Keep Active", placeholder: "October invoice unpaid",
  },
  activate: {
    title: (name: string) => `Activate ${name}?`,
    text: "Everyone at the gym can use the app again, and its messages start going out.",
    button: "Activate Gym", busy: "Activating…", keep: "Cancel", placeholder: "Paid in full",
  },
};

/** Suspend or Activate, with the reason kept in the gym's history. */
export function StatusSheet({ gym, change, onClose }: { gym: GymDetail; change: "suspend" | "activate" | null; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const copy = STATUS_COPY[change ?? "suspend"];
  const close = () => { setReason(""); setErr(undefined); a.clearError(); onClose(); };
  async function go() {
    if (!reason.trim()) return setErr("Say why, for the gym's history");
    try { await a.run(`${GYMS}${gym.id}/${change}/`, { reason: reason.trim() }, { refresh: [GYMS] }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={change !== null} onClose={close} title={copy.title(gym.name)}>
      <p className="rl-row__meta">{copy.text}</p>
      <Field label="Reason" error={err ?? fieldError(a.error, "reason")} hint="Kept in the gym's history.">
        {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={reason} placeholder={copy.placeholder} maxLength={200} onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}
      </Field>
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions">
        <button className={`rl-button rl-button--block${change === "suspend" ? " rl-button--danger" : ""}`} type="button" disabled={a.busy} onClick={go}>{a.busy ? copy.busy : copy.button}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={close}>{copy.keep}</button>
      </div>
    </Sheet>
  );
}
