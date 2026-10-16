"use client";
import { Plus, Tag } from "lucide-react";
import { useState } from "react";

import type { Offer, Plan } from "@/api/gen/model";
import { useOffersList } from "@/api/gen/offers/offers";
import { usePlansList } from "@/api/gen/plans/plans";
import { PageBar } from "@/components/shell";
import { Choices, ErrorText, Field, Icon, Section, Seg, Sheet, SkeletonRows } from "@/components/ui";
import { months } from "@/features/sell";
import { day, isoDate, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

export default function PlansPage() {
  const { role } = useSession();
  const admin = role.role === "admin";
  const plans = usePlansList({ limit: 100 });
  const offers = useOffersList({ limit: 100 });
  const [planSheet, setPlanSheet] = useState<Plan | "new" | null>(null);
  const [offerSheet, setOfferSheet] = useState<Offer | "new" | null>(null);
  const today = isoDate(new Date());
  const list = plans.data?.data.results ?? [];
  const planName = (id: number) => list.find((p) => p.id === id)?.name ?? "";
  return (
    <div className="rl-app rl-root">
      <PageBar title="Plans and offers" sub={admin ? "What the desk can sell" : "What you can sell"} back="/more" />
      <main className="rl-app__main">
        <Section title="Plans" aside={admin ? <button className="rl-link rl-link--plain" type="button" onClick={() => setPlanSheet("new")}><span>Add Plan</span></button> : undefined}>
          {plans.isLoading ? <SkeletonRows n={4} /> : (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {list.map((p) => (
                <li key={p.id}><button className="rl-mrow" type="button" disabled={!admin} onClick={() => setPlanSheet(p)}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Tag} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{p.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{months(p)}{p.includes ? ` • ${p.includes}` : ""}{p.on_sale ? "" : " • Not on sale"}</span>
                  <span className="rl-mrow__time">{rupees(p.price_paise)}</span>
                </button></li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Offers" aside={admin ? <button className="rl-link rl-link--plain" type="button" onClick={() => setOfferSheet("new")}><span>Add Offer</span></button> : undefined}>
          {(offers.data?.data.results ?? []).length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {(offers.data?.data.results ?? []).map((o) => {
                const live = o.is_active && o.starts <= today && o.ends >= today;
                return (
                  <li key={o.id}><button className="rl-mrow" type="button" disabled={!admin} onClick={() => setOfferSheet(o)}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Tag} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{o.name}</span>
                    <span className="rl-row__meta rl-mrow__meta">{o.percent_off != null ? `${o.percent_off}% off` : `${rupees(o.amount_off_paise)} off`} • {o.plans?.length ? o.plans.map(planName).join(", ") : "Every plan"} • {day(o.starts)} to {day(o.ends)}</span>
                    <span className={`rl-status ${live ? "rl-status--active" : "rl-status--off"}`}>{live ? "Running" : o.is_active ? (o.starts > today ? "Upcoming" : "Ended") : "Off"}</span>
                  </button></li>
                );
              })}
            </ul>
          ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No offers. Offers are the only way the desk can give a discount.</p></div>}
        </Section>
        {admin && (
          <Section label="Add">
            <div className="rl-actions">
              <button className="rl-button rl-button--secondary" type="button" onClick={() => setPlanSheet("new")}><Icon as={Plus} />Add Plan</button>
              <button className="rl-button rl-button--secondary" type="button" onClick={() => setOfferSheet("new")}><Icon as={Plus} />Add Offer</button>
            </div>
          </Section>
        )}
      </main>
      {admin && <PlanSheet plan={planSheet} onClose={() => setPlanSheet(null)} />}
      {admin && <OfferSheet offer={offerSheet} plans={list} onClose={() => setOfferSheet(null)} />}
    </div>
  );
}

function PlanSheet({ plan, onClose }: { plan: Plan | "new" | null; onClose: () => void }) {
  const edit = plan && plan !== "new" ? plan : null;
  const [f, setF] = useState({ name: "", kind: "membership" as "membership" | "pt", months: "1", sessions: "12", price: "", includes: "" });
  const [key, setKey] = useState<unknown>(null);
  if (plan !== key) { // reset the form when a different plan opens
    setKey(plan);
    setF(edit ? { name: edit.name, kind: (edit.kind ?? "membership") as "membership" | "pt", months: String(edit.months ?? 1), sessions: String(edit.sessions ?? 12), price: String(edit.price_paise / 100), includes: edit.includes ?? "" } : { name: "", kind: "membership", months: "1", sessions: "12", price: "", includes: "" });
  }
  const a = useAction();
  async function save(extra?: object) {
    const body = { name: f.name.trim(), kind: f.kind, months: Number(f.months) || 0, sessions: f.kind === "pt" ? Number(f.sessions) || 0 : 0, price_paise: toPaise(f.price), includes: f.includes, ...extra };
    try { await a.run(edit ? `/api/plans/${edit.id}/` : "/api/plans/", body, { method: edit ? "PATCH" : "POST", refresh: ["/api/plans/"] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!plan} onClose={onClose} title={edit ? "Edit Plan" : "Add Plan"}>
      <Seg label="Kind" value={f.kind} onChange={(v) => setF({ ...f, kind: v })} options={[{ value: "membership", label: "Membership" }, { value: "pt", label: "Personal training" }]} />
      <Field label="Name" error={fieldError(a.error, "name")}>{(id) => <input className="rl-field__input" id={id} value={f.name} placeholder="Quarterly" onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
      <div className="rl-pair">
        <Field label="Months" error={fieldError(a.error, "months")}>{(id) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={1} value={f.months} onChange={(e) => setF({ ...f, months: e.target.value })} />}</Field>
        {f.kind === "pt" && <Field label="Sessions" error={fieldError(a.error, "sessions")}>{(id) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={1} value={f.sessions} onChange={(e) => setF({ ...f, sessions: e.target.value })} />}</Field>}
      </div>
      <Field label="Price" prefix="₹" error={fieldError(a.error, "price_paise")}>{(id) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" value={f.price} placeholder="4500" onChange={(e) => setF({ ...f, price: e.target.value })} />}</Field>
      <Field label="Includes" optional>{(id) => <input className="rl-field__input" id={id} value={f.includes} placeholder="Gym floor, lockers" onChange={(e) => setF({ ...f, includes: e.target.value })} />}</Field>
      {edit && <p className="rl-field__hint">A new price applies to new sales. Members already on this plan keep what they bought.</p>}
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => save()}>{edit ? "Save Changes" : "Add Plan"}</button>
        {edit && <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={() => save({ on_sale: !edit.on_sale })}>{edit.on_sale ? "Stop Selling" : "Sell Again"}</button>}
      </div>
    </Sheet>
  );
}

function OfferSheet({ offer, plans, onClose }: { offer: Offer | "new" | null; plans: Plan[]; onClose: () => void }) {
  const edit = offer && offer !== "new" ? offer : null;
  const blank = { name: "", type: "percent" as "percent" | "amount", value: "", starts: isoDate(new Date()), ends: "", plans: [] as number[] };
  const [f, setF] = useState(blank);
  const [key, setKey] = useState<unknown>(null);
  if (offer !== key) {
    setKey(offer);
    setF(edit ? { name: edit.name, type: edit.percent_off != null ? "percent" : "amount", value: String(edit.percent_off ?? (edit.amount_off_paise ?? 0) / 100), starts: edit.starts, ends: edit.ends, plans: edit.plans ?? [] } : blank);
  }
  const a = useAction();
  async function save(extra?: object) {
    const v = Number(f.value) || 0;
    const body = { name: f.name.trim(), percent_off: f.type === "percent" ? v : null, amount_off_paise: f.type === "amount" ? toPaise(v) : null, starts: f.starts, ends: f.ends, plans: f.plans, ...extra };
    try { await a.run(edit ? `/api/offers/${edit.id}/` : "/api/offers/", body, { method: edit ? "PATCH" : "POST", refresh: ["/api/offers/"] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!offer} onClose={onClose} title={edit ? "Edit Offer" : "Add Offer"}>
      <Field label="Name" error={fieldError(a.error, "name")}>{(id) => <input className="rl-field__input" id={id} value={f.name} placeholder="Diwali 15% off" onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
      <Choices name="otype" two value={f.type} onChange={(v) => setF({ ...f, type: v })} options={[{ value: "percent", title: "Percent off" }, { value: "amount", title: "Amount off" }]} />
      <Field label={f.type === "percent" ? "Percent off" : "Amount off"} prefix={f.type === "amount" ? "₹" : undefined} error={fieldError(a.error, "percent_off") ?? fieldError(a.error, "amount_off_paise")}>
        {(id) => <input className="rl-field__input" id={id} type="number" inputMode="numeric" value={f.value} placeholder={f.type === "percent" ? "15" : "500"} onChange={(e) => setF({ ...f, value: e.target.value })} />}
      </Field>
      <div className="rl-pair">
        <Field label="Starts">{(id) => <input className="rl-field__input" id={id} type="date" value={f.starts} onChange={(e) => setF({ ...f, starts: e.target.value })} />}</Field>
        <Field label="Ends" error={fieldError(a.error, "ends")}>{(id) => <input className="rl-field__input" id={id} type="date" value={f.ends} onChange={(e) => setF({ ...f, ends: e.target.value })} />}</Field>
      </div>
      <fieldset className="rl-fieldset"><legend>Plans <span className="rl-optional">(none chosen means every plan)</span></legend>
        <div className="rl-chips">
          {plans.map((p) => (
            <label className="rl-chipopt" key={p.id}><input type="checkbox" checked={f.plans.includes(p.id)} onChange={(e) => setF({ ...f, plans: e.target.checked ? [...f.plans, p.id] : f.plans.filter((x) => x !== p.id) })} /><span>{p.name}</span></label>
          ))}
        </div>
      </fieldset>
      <ErrorText>{a.error && !a.error.fields ? a.error.message : a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => save()}>{edit ? "Save Changes" : "Add Offer"}</button>
        {edit && <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={() => save({ is_active: !edit.is_active })}>{edit.is_active ? "Switch Off" : "Switch On"}</button>}
      </div>
    </Sheet>
  );
}
