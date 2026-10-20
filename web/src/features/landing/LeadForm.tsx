"use client";
/* Book a Free Demo: the landing page's one form. Short on purpose; each field says what to fix in the API's own
 * words, and the first wrong one takes focus. */
import { Check, MessageCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useLeadsCreate } from "@/api/gen/leads/leads";
import type { LeadBranchesEnum } from "@/api/gen/model";
import { Chips, ErrorText, Field, Icon } from "@/components/ui";
import { ApiError } from "@/lib/api";
import { phone as showPhone } from "@/lib/format";
import { fieldError } from "@/lib/hooks";
import { campaignTags, checkLead, EMPTY_LEAD, LEAD_FIELDS, mobileDigits, type LeadField, type LeadForm as Form } from "@/lib/leads";
import { SALES_WHATSAPP, whatsappLink } from "@/lib/site";

import s from "./landing.module.css";

const BRANCHES: { value: LeadBranchesEnum; label: string }[] = [{ value: "1", label: "1" }, { value: "2-3", label: "2 to 3" }, { value: "4+", label: "4 or more" }];

export function LeadForm() {
  const [f, setF] = useState<Form>(EMPTY_LEAD);
  const [errors, setErrors] = useState<Partial<Record<LeadField, string>>>({});
  const [sent, setSent] = useState<Form | null>(null);
  const trap = useRef<HTMLInputElement>(null);
  const fields = useRef<Partial<Record<LeadField, HTMLElement | null>>>({});
  const done = useRef<HTMLHeadingElement>(null);
  const ask = useLeadsCreate();
  const failure = ask.error instanceof ApiError ? ask.error : ask.error ? new ApiError(0, "network", "Can’t reach Dumbelo. Check your connection and try again.") : null;

  useEffect(() => { if (sent) done.current?.focus(); }, [sent]);

  const set = (k: LeadField) => (v: string) => { setF((x) => ({ ...x, [k]: v })); setErrors((x) => ({ ...x, [k]: undefined })); };
  const errorOf = (k: LeadField) => errors[k] ?? fieldError(failure, k);
  const focusFirst = (bad: Partial<Record<string, unknown>>) => {
    const first = LEAD_FIELDS.find((k) => bad[k]);
    const el = first && fields.current[first];
    (el instanceof HTMLInputElement ? el : el?.querySelector("input"))?.focus();
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const bad = checkLead(f);
    setErrors(bad);
    if (Object.keys(bad).length) return focusFirst(bad);
    try {
      await ask.mutateAsync({
        data: {
          name: f.name.trim(), phone: mobileDigits(f.phone), gym_name: f.gym_name.trim(), city: f.city.trim(),
          branches: f.branches as LeadBranchesEnum, email: f.email.trim(), website: trap.current?.value ?? "", ...campaignTags(window.location.search),
        },
      });
      setSent(f);
    } catch (err) {
      if (err instanceof ApiError && err.fields) focusFirst(err.fields);
    }
  }

  if (sent) {
    return (
      <div className={s.formDone} role="status">
        <span className={s.formDoneTick} aria-hidden="true"><Icon as={Check} /></span>
        <h3 ref={done} tabIndex={-1} className={s.formTitle}>Thanks, {sent.name.trim().split(" ")[0]}. We&apos;ll call you soon.</h3>
        <p className={s.cardText}>
          We&apos;ll ring {showPhone(mobileDigits(sent.phone))} to find a time that suits you, and show you Dumbelo with
          {sent.branches === "1" ? " your branch" : " your branches"} in mind.
        </p>
        {SALES_WHATSAPP && (
          <a className="rl-button rl-button--secondary rl-button--block" href={whatsappLink(`Hi, I just asked for a demo of Dumbelo for ${sent.gym_name.trim()}.`)} target="_blank" rel="noopener noreferrer">
            <Icon as={MessageCircle} size="sm" />Message Us on WhatsApp
          </a>
        )}
      </div>
    );
  }

  return (
    <form className={s.form} noValidate onSubmit={submit} aria-labelledby="demo-form-title">
      <h3 id="demo-form-title" className={s.formTitle}>Book a free demo</h3>
      <p className={s.formLede}>Takes a minute. We&apos;ll call you to set up a time.</p>
      <div ref={(el) => { fields.current.name = el; }}>
        <Field label="Your name" error={errorOf("name")}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} aria-invalid={!!errorOf("name")} name="name" autoComplete="name" enterKeyHint="next" maxLength={100} value={f.name} onChange={(e) => set("name")(e.target.value)} />}
        </Field>
      </div>
      <div ref={(el) => { fields.current.phone = el; }}>
        <Field label="Mobile number" prefix="+91" error={errorOf("phone")}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} aria-invalid={!!errorOf("phone")} name="phone" type="tel" inputMode="tel" autoComplete="tel-national" enterKeyHint="next" maxLength={16} placeholder="98765 43210" value={f.phone} onChange={(e) => set("phone")(e.target.value)} />}
        </Field>
      </div>
      <div className={s.formPair}>
        <div ref={(el) => { fields.current.gym_name = el; }}>
          <Field label="Gym name" error={errorOf("gym_name")}>
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} aria-invalid={!!errorOf("gym_name")} name="organization" autoComplete="organization" enterKeyHint="next" maxLength={120} value={f.gym_name} onChange={(e) => set("gym_name")(e.target.value)} />}
          </Field>
        </div>
        <div ref={(el) => { fields.current.city = el; }}>
          <Field label="City" error={errorOf("city")}>
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} aria-invalid={!!errorOf("city")} name="city" autoComplete="address-level2" enterKeyHint="next" maxLength={80} value={f.city} onChange={(e) => set("city")(e.target.value)} />}
          </Field>
        </div>
      </div>
      <fieldset className={s.formChoice} ref={(el) => { fields.current.branches = el; }} aria-describedby={errorOf("branches") ? "branches-e" : undefined}>
        <legend className="rl-field__label">How many branches?</legend>
        <Chips name="branches" label="How many branches?" scroll={false} value={f.branches} onChange={set("branches")} options={BRANCHES} />
        <ErrorText id="branches-e">{errorOf("branches")}</ErrorText>
      </fieldset>
      <div ref={(el) => { fields.current.email = el; }}>
        <Field label="Email" optional error={errorOf("email")}>
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} aria-invalid={!!errorOf("email")} name="email" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" spellCheck={false} enterKeyHint="send" maxLength={254} placeholder="you@gym.com" value={f.email} onChange={(e) => set("email")(e.target.value)} />}
        </Field>
      </div>
      {/* Left empty by people, who never see it; bots fill every field they find. */}
      <div className={s.trap} aria-hidden="true">
        <label>Website<input ref={trap} name="website" type="text" tabIndex={-1} autoComplete="off" /></label>
      </div>
      <ErrorText>{failure && !failure.fields ? failure.message : undefined}</ErrorText>
      <button className={`rl-button rl-button--block${ask.isPending ? " is-loading" : ""}`} type="submit" disabled={ask.isPending} aria-busy={ask.isPending}>
        <span className="rl-button__spinner" aria-hidden="true" />{ask.isPending ? "Booking…" : "Book My Free Demo"}
      </button>
      <p className={s.formNote}>No card and no commitment. We use your number only to arrange the demo.</p>
    </form>
  );
}
