"use client";
/* The Console's WhatsApp: an account's fields, its sheets (Edit Details, Replace Credentials) and its templates. */
import { Plus, X } from "lucide-react";
import { useState } from "react";

import type { MessageKind, WhatsAppAccount, WhatsAppTemplate } from "@/api/gen/model";
import { usePlatformWhatsappTemplatesKindsList } from "@/api/gen/platform/platform";
import { ErrorText, Field, Icon, Seg, Sheet } from "@/components/ui";
import { TEMPLATE_STATUS, WHATSAPP_STATUS } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

export const ACCOUNTS = "/api/platform/whatsapp-accounts/";
export const TEMPLATES = "/api/platform/whatsapp-templates/";
const REFRESH = [ACCOUNTS, TEMPLATES];

export function Badge({ of, status }: { of: "account" | "template"; status: string }) {
  const s = (of === "account" ? WHATSAPP_STATUS : TEMPLATE_STATUS)[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

export const accountTitle = (a: Pick<WhatsAppAccount, "is_shared" | "gym_name">) => (a.is_shared ? "Rackline's shared number" : a.gym_name ?? "A gym's own number");

export type Where = { waba_id: string; phone_number_id: string; display_number: string };
const DIGITS = /^\d{5,32}$/;

/** Checks the three ids before they go: Meta's ids are long numbers, so a pasted number or URL is caught here. */
export function whereErrors(f: Where): Record<string, string> {
  const e: Record<string, string> = {};
  if (!DIGITS.test(f.waba_id.trim())) e.waba_id = "Use the WhatsApp Business account id from Meta: digits only";
  if (!DIGITS.test(f.phone_number_id.trim())) e.phone_number_id = "Use the phone number id from Meta (not the number itself): digits only";
  if (!/^\+?[\d ()-]{6,23}$/.test(f.display_number.trim())) e.display_number = "Type the number as people see it, e.g. +91 98000 00000";
  return e;
}

/** Where an account points: the number people see, and Meta's two ids for it. */
export function WhereFields({ f, set, err }: { f: Where; set: (f: Where) => void; err: (k: string) => string | undefined }) {
  const on = (k: keyof Where) => (e: React.ChangeEvent<HTMLInputElement>) => set({ ...f, [k]: e.target.value });
  return (
    <>
      <Field label="Number" error={err("display_number")} hint="As people see it on WhatsApp. Test Connection fills it in from Meta.">
        {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="tel" inputMode="tel" autoComplete="off" value={f.display_number} placeholder="+91 98000 00000" onChange={on("display_number")} />}
      </Field>
      <Field label="Phone number id" error={err("phone_number_id")} hint="In Meta's WhatsApp Manager, under the number's API setup.">
        {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} inputMode="numeric" autoComplete="off" spellCheck={false} value={f.phone_number_id} onChange={on("phone_number_id")} />}
      </Field>
      <Field label="WhatsApp Business account id" error={err("waba_id")}>
        {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} inputMode="numeric" autoComplete="off" spellCheck={false} value={f.waba_id} onChange={on("waba_id")} />}
      </Field>
    </>
  );
}

/** A credential typed in: never shown again, so it's a password field the browser won't save. */
export function SecretField({ label, value, onChange, error, hint, optional }: {
  label: string; value: string; onChange: (v: string) => void; error?: string; hint?: string; optional?: boolean;
}) {
  return (
    <Field label={label} error={error} hint={hint} optional={optional}>
      {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="password" autoComplete="new-password" autoCapitalize="none" spellCheck={false} value={value} onChange={(e) => onChange(e.target.value)} />}
    </Field>
  );
}

function useFreshOnOpen<T>(open: boolean, fresh: () => T): [T, (v: T) => void] {
  const [f, setF] = useState(fresh);
  const [was, setWas] = useState(false);
  if (open !== was) { // start from what's saved each time the sheet opens
    setWas(open);
    if (open) setF(fresh());
  }
  return [f, setF];
}

/** Edit Details: the number and Meta's ids. New ids mean testing it again. */
export function EditAccountSheet({ account, open, onClose }: { account: WhatsAppAccount; open: boolean; onClose: () => void }) {
  const [f, setF] = useFreshOnOpen<Where>(open, () => ({ waba_id: account.waba_id, phone_number_id: account.phone_number_id, display_number: account.display_number }));
  const [errs, setErrs] = useState<Record<string, string>>({});
  const a = useAction();
  const close = () => { setErrs({}); a.clearError(); onClose(); };
  async function save() {
    const e = whereErrors(f);
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = { waba_id: f.waba_id.trim(), phone_number_id: f.phone_number_id.trim(), display_number: f.display_number.trim() };
    try { await a.run(`${ACCOUNTS}${account.id}/`, body, { method: "PATCH", refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Edit Details">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <WhereFields f={f} set={setF} err={(k) => errs[k] ?? fieldError(a.error, k)} />
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
      </form>
    </Sheet>
  );
}

/** Replace Credentials: a new access token, app secret or both. What's left empty stays as it is. */
export function CredentialsSheet({ account, open, onClose }: { account: WhatsAppAccount; open: boolean; onClose: () => void }) {
  const [f, setF] = useFreshOnOpen(open, () => ({ access_token: "", app_secret: "" }));
  const [err, setErr] = useState<string>();
  const a = useAction();
  const close = () => { setErr(undefined); a.clearError(); onClose(); };
  async function save() {
    const body = { access_token: f.access_token.trim() || undefined, app_secret: f.app_secret.trim() || undefined };
    if (!body.access_token && !body.app_secret) return setErr("Paste a new access token, a new app secret, or both");
    setErr(undefined);
    try { await a.run(`${ACCOUNTS}${account.id}/replace-credentials/`, body, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Replace Credentials">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <SecretField label="Access token" optional value={f.access_token} onChange={(access_token) => setF({ ...f, access_token })}
          error={err ?? fieldError(a.error, "access_token")} hint={`Now ending in ${account.access_token_last4}. Leave it empty to keep it.`} />
        <SecretField label="App secret" optional value={f.app_secret} onChange={(app_secret) => setF({ ...f, app_secret })}
          error={fieldError(a.error, "app_secret")} hint={`Now ending in ${account.app_secret_last4}. Leave it empty to keep it.`} />
        <p className="rl-row__meta">They&apos;re kept encrypted and never shown again, only their last 4 characters. Run Test Connection after.</p>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Credentials"}</button></div>
      </form>
    </Sheet>
  );
}

type TemplateForm = { kind: string; name: string; language: string; category: string; body: string; parameters: string[]; status: string };
const CATEGORIES = [{ value: "utility", label: "Utility" }, { value: "marketing", label: "Marketing" }, { value: "authentication", label: "Sign-in" }];

function templateErrors(f: TemplateForm): Record<string, string> {
  const e: Record<string, string> = {};
  if (!/^[a-z0-9_]{1,512}$/.test(f.name.trim())) e.name = "Use the name exactly as it is in Meta: lower-case letters, numbers and _";
  if (!/^[a-z]{2,3}(_[A-Z]{2})?$/.test(f.language.trim())) e.language = "Use Meta's language code, e.g. en or en_US";
  const found = new Set(Array.from(f.body.matchAll(/\{\{\s*(\d+)\s*\}\}/g), (m) => Number(m[1])));
  const want = f.parameters.map((_, i) => i + 1);
  if (!f.body.trim()) e.body = "Paste the text as Meta approved it";
  else if (found.size !== want.length || want.some((n) => !found.has(n))) {
    e.body = want.length ? `With ${want.length} details, the text needs ${want.map((n) => `{{${n}}}`).join(", ")}` : "With no details, the text has no {{n}}";
  }
  return e;
}

/** The details that fill {{1}}, {{2}}… in order: tap one to add it, × to take it out. */
function ParameterPicker({ kind, value, onChange, error }: { kind?: MessageKind; value: string[]; onChange: (v: string[]) => void; error?: string }) {
  const label = (name: string) => kind?.parameters.find((p) => p.name === name)?.label ?? name;
  const left = (kind?.parameters ?? []).filter((p) => !value.includes(p.name));
  return (
    <fieldset className="rl-fieldset"><legend>Details, in order</legend>
      {value.length > 0 && (
        <ul className="rl-card rl-mlist rl-mlist--compact">
          {value.map((name, i) => (
            <li key={name}><div className="rl-mrow">
              <span className="rl-pill" aria-hidden="true">{`{{${i + 1}}}`}</span>
              <span className="rl-row__title rl-mrow__name">{label(name)}</span>
              <span className="rl-row__meta rl-mrow__meta">{name}</span>
              <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Take out ${label(name)}`} onClick={() => onChange(value.filter((v) => v !== name))}><Icon as={X} size="sm" /></button>
            </div></li>
          ))}
        </ul>
      )}
      {left.length > 0 && (
        <div className="rl-chips" role="group" aria-label="Add a detail">
          {left.map((p) => (
            <button key={p.name} className="rl-chip" type="button" onClick={() => onChange([...value, p.name])}><Icon as={Plus} size="xs" />{p.label}</button>
          ))}
        </div>
      )}
      <ErrorText>{error}</ErrorText>
      <p className="rl-field__hint">In the order they appear in Meta&apos;s template: the first goes in {"{{1}}"}.</p>
    </fieldset>
  );
}

const fieldsOf = (t: WhatsAppTemplate | null, kind: string): TemplateForm => t
  ? { kind: t.kind, name: t.name, language: t.language, category: t.category, body: t.body, parameters: [...t.parameters], status: t.status }
  : { kind, name: "", language: "en", category: "utility", body: "", parameters: [], status: "pending" };

/** Add Template (no `template`) or Edit Template: which message it is, its name in Meta, the approved text and
 *  which detail fills each {{n}}. Its status is copied from Meta's dashboard. */
export function TemplateSheet({ accountId, template, open, onClose }: { accountId: number; template: WhatsAppTemplate | null; open: boolean; onClose: () => void }) {
  const kinds = usePlatformWhatsappTemplatesKindsList().data?.data ?? [];
  const [f, setF] = useFreshOnOpen<TemplateForm>(open, () => fieldsOf(template, kinds[0]?.kind ?? "plan_ending"));
  const [errs, setErrs] = useState<Record<string, string>>({});
  const a = useAction();
  const kind = kinds.find((k) => k.kind === f.kind);
  const err = (k: string) => errs[k] ?? fieldError(a.error, k);
  const close = () => { setErrs({}); a.clearError(); onClose(); };
  async function save() {
    const e = templateErrors(f);
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = { ...f, name: f.name.trim(), language: f.language.trim(), body: f.body.trim() };
    try {
      if (template) await a.run(`${TEMPLATES}${template.id}/`, body, { method: "PATCH", refresh: REFRESH });
      else await a.run(TEMPLATES, { ...body, account: accountId }, { refresh: REFRESH });
      close();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={template ? "Edit Template" : "Add Template"}>
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Message" error={err("kind")}>
          {(id, d) => (
            <select className="rl-field__input" id={id} aria-describedby={d} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value, parameters: [] })}>
              {kinds.map((k) => <option key={k.kind} value={k.kind}>{k.label}</option>)}
            </select>
          )}
        </Field>
        <Field label="Name in Meta" error={err("name")}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} autoCapitalize="none" autoCorrect="off" spellCheck={false} value={f.name} placeholder="plan_ending_v1" onChange={(e) => setF({ ...f, name: e.target.value })} />}
        </Field>
        <Field label="Language" error={err("language")} hint="Meta's code for it: en, en_US, hi…">
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} autoCapitalize="none" autoCorrect="off" spellCheck={false} value={f.language} onChange={(e) => setF({ ...f, language: e.target.value })} />}
        </Field>
        <fieldset className="rl-fieldset"><legend>Category in Meta</legend>
          <Seg label="Category" value={f.category} onChange={(category) => setF({ ...f, category })} options={CATEGORIES} />
        </fieldset>
        <Field label="Text" area error={err("body")} hint="As Meta approved it, with {{1}}, {{2}}… where the details go.">
          {(id, d) => <textarea className="rl-field__input" id={id} aria-describedby={d} rows={4} value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })} />}
        </Field>
        <ParameterPicker kind={kind} value={f.parameters} onChange={(parameters) => setF({ ...f, parameters })} error={err("parameters")} />
        <Field label="Status in Meta" error={err("status")} hint="Only an approved template is sent, one per message and language.">
          {(id, d) => (
            <select className="rl-field__input" id={id} aria-describedby={d} value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })}>
              {Object.entries(TEMPLATE_STATUS).map(([v, s]) => <option key={v} value={v}>{s.label}</option>)}
            </select>
          )}
        </Field>
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : template ? "Save Changes" : "Add Template"}</button></div>
      </form>
    </Sheet>
  );
}
