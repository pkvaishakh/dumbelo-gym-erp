"use client";
/* A gym's admin accounts in the Console: the list, Add Admin, and each admin's actions. */
import { AtSign, Mail, Phone } from "lucide-react";
import { useState } from "react";

import type { GymAdmin } from "@/api/gen/model";
import { usePlatformGymsAdminsList } from "@/api/gen/platform/platform";
import { Details, ErrorText, Field, Photo, Section, Sheet, SkeletonRows, Status } from "@/components/ui";
import { phone, plural } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

import { cleanUsername, ExistingLoginField, type LoginKind, LoginKindChips, UsernameField } from "../username";

const refresh = (gymId: number) => [`/api/platform/gyms/${gymId}/`];

export function AdminsSection({ gymId }: { gymId: number }) {
  const q = usePlatformGymsAdminsList(gymId);
  const rows = q.data?.data ?? [];
  const [open, setOpen] = useState<GymAdmin | null>(null);
  const [adding, setAdding] = useState(false);
  const current = open && rows.find((r) => r.id === open.id); // follows the list after each change
  return (
    <Section title="Admins" aside={<button className="rl-link rl-link--plain" type="button" onClick={() => setAdding(true)}><span>Add Admin</span></button>}>
      {q.isLoading ? <SkeletonRows n={2} /> : q.isError ? (
        <div className="rl-card rl-card--pad"><ErrorText>{q.error instanceof Error ? q.error.message : "Can't load the admins."}</ErrorText></div>
      ) : rows.length ? (
        <ul className="rl-card rl-mlist rl-mlist--compact">
          {rows.map((r) => (
            <li key={r.id}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => setOpen(r)}>
              <Photo name={r.name} />
              <span className="rl-row__title rl-mrow__name">{r.name}</span>
              <span className="rl-row__meta rl-mrow__meta">@{r.username}{r.other_gyms ? ` • also ${plural(r.other_gyms, "other gym")}` : ""}</span>
              {r.is_owner ? <span className="rl-tag">Owner</span> : !r.is_active && <Status status="off" />}
            </button></li>
          ))}
        </ul>
      ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No admins yet. Add one so the gym can sign in.</p></div>}
      {current && <AdminSheet gymId={gymId} admin={current} onClose={() => setOpen(null)} />}
      <AddAdminSheet gymId={gymId} open={adding} onClose={() => setAdding(false)} />
    </Section>
  );
}

type Step = "menu" | "password" | "owner" | "deactivate" | "reset-done";

function AdminSheet({ gymId, admin, onClose }: { gymId: number; admin: GymAdmin; onClose: () => void }) {
  const [step, setStep] = useState<Step>("menu");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const url = `/api/platform/gyms/${gymId}/admins/${admin.id}/`;
  const back = () => { setStep("menu"); setErr(undefined); a.clearError(); };
  async function act(path: string) {
    try { await a.run(url + path, undefined, { refresh: refresh(gymId) }); back(); } catch { /* shown */ }
  }
  async function reset() {
    if (pw.length < 8) return setErr("Use at least 8 characters");
    try { await a.run(url + "reset-password/", { password: pw }, { refresh: [] }); setPw(""); setStep("reset-done"); } catch { /* shown */ }
  }
  const failed = <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>;
  const shared = admin.other_gyms ? ` The same login opens ${plural(admin.other_gyms, "other gym")}, and the new password works there too.` : "";
  return (
    <Sheet open onClose={onClose} title={step === "reset-done" ? undefined : admin.name}>
      {step === "menu" && (
        <>
          <p className="rl-row__meta">{admin.is_owner ? "The account owner: they look after the gym's Dumbelo plan and can't be deactivated." : admin.is_active ? "An admin of this gym." : "Deactivated: they can't open this gym."}</p>
          <Details rows={[{ icon: AtSign, label: "Username", value: `@${admin.username}` }, { icon: Mail, label: "Email", value: admin.email || "Not set" }, { icon: Phone, label: "Mobile number", value: phone(admin.phone) }]} />
          {failed}
          <div className="rl-sheet__actions">
            {admin.is_active && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setStep("password")}>Reset Password</button>}
            {admin.is_active && !admin.is_owner && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setStep("owner")}>Make Owner</button>}
            {admin.is_active && !admin.is_owner && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setStep("deactivate")}>Deactivate</button>}
            {!admin.is_active && <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => act("reactivate/")}>{a.busy ? "Saving…" : "Reactivate"}</button>}
          </div>
        </>
      )}
      {step === "password" && (
        <>
          <p className="rl-row__meta">For when they&apos;ve lost theirs. They&apos;re signed out on every phone and computer.{shared}</p>
          <Field label="New password" error={err ?? fieldError(a.error, "password")} hint="At least 8 characters. Tell them the password.">
            {(id) => <input className="rl-field__input" id={id} type="text" autoComplete="new-password" autoCapitalize="none" spellCheck={false} value={pw} onChange={(e) => { setPw(e.target.value); setErr(undefined); }} />}
          </Field>
          {failed}
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={reset}>{a.busy ? "Saving…" : "Set Password"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={back}>Back</button>
          </div>
        </>
      )}
      {step === "reset-done" && (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">Password reset</h2><p className="rl-confirm__text">{admin.name} signs in as @{admin.username} with the password you set.</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={onClose}>Done</button></div>
        </>
      )}
      {step === "owner" && (
        <>
          <p className="rl-row__meta">{admin.name} becomes the account owner: they look after the gym&apos;s Dumbelo plan and can&apos;t be deactivated. The current owner stays an admin.</p>
          {failed}
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => act("make-owner/")}>{a.busy ? "Saving…" : "Make Owner"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={back}>Back</button>
          </div>
        </>
      )}
      {step === "deactivate" && (
        <>
          <p className="rl-row__meta">They can&apos;t open this gym until you reactivate them. Their history stays.</p>
          {failed}
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={() => act("deactivate/")}>{a.busy ? "Saving…" : "Deactivate"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={back}>Keep Active</button>
          </div>
        </>
      )}
    </Sheet>
  );
}

function AddAdminSheet({ gymId, open, onClose }: { gymId: number; open: boolean; onClose: () => void }) {
  const blank = { existing_username: "", username: "", email: "", name: "", password: "" };
  const [f, setF] = useState(blank);
  const [kind, setKind] = useState<LoginKind>("new");
  const [err, setErr] = useState<string>();
  const [added, setAdded] = useState<GymAdmin | null>(null);
  const a = useAction();
  const close = () => { setF(blank); setKind("new"); setErr(undefined); setAdded(null); a.clearError(); onClose(); };
  async function save() {
    if (kind === "existing" && !cleanUsername(f.existing_username)) return setErr("Enter the username they sign in with");
    if (kind === "new" && f.email.trim() && !/^\S+@\S+\.\S+$/.test(f.email.trim())) return setErr("Enter an email like name@gym.in, or leave it empty");
    const body = kind === "existing" ? { existing_username: cleanUsername(f.existing_username) }
      : { username: cleanUsername(f.username), email: f.email.trim(), name: f.name, password: f.password };
    try { setAdded((await a.run<GymAdmin>(`/api/platform/gyms/${gymId}/admins/`, body, { refresh: refresh(gymId) }))!); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={added ? undefined : "Add Admin"}>
      {added ? (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">{added.name} is an admin</h2>
            <p className="rl-confirm__text">They can open {added.other_gyms ? "this gym with their other gyms" : "the gym"} now, signing in as @{added.username}.</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <LoginKindChips value={kind} onChange={(k) => { setKind(k); setErr(undefined); a.clearError(); }} />
          {kind === "existing" ? (
            <ExistingLoginField value={f.existing_username} onChange={(v) => { setF({ ...f, existing_username: v }); setErr(undefined); }} error={err ?? fieldError(a.error, "existing_username")} />
          ) : (
            <>
              <Field label="Name" error={fieldError(a.error, "name")}>
                {(id) => <input className="rl-field__input" id={id} autoComplete="off" autoCapitalize="words" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}
              </Field>
              <Field label="Email" optional error={err ?? fieldError(a.error, "email")}>
                {(id) => <input className="rl-field__input" id={id} type="email" inputMode="email" autoComplete="off" autoCapitalize="none" value={f.email} onChange={(e) => { setF({ ...f, email: e.target.value }); setErr(undefined); }} />}
              </Field>
              <UsernameField value={f.username} onChange={(v) => setF({ ...f, username: v })} email={f.email} name={f.name} error={fieldError(a.error, "username")} />
              <Field label="First password" error={fieldError(a.error, "password")} hint="Tell them, and they change it from More.">
                {(id) => <input className="rl-field__input" id={id} type="text" autoComplete="new-password" autoCapitalize="none" spellCheck={false} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />}
              </Field>
            </>
          )}
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Adding…" : "Add Admin"}</button></div>
        </form>
      )}
    </Sheet>
  );
}
