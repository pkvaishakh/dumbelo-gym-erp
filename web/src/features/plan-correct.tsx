"use client";
/* Edit Membership: an admin corrects a plan already sold (its plan, offer, dates or price), with a reason the audit log
   keeps. A new plan or offer works the price out again, and a new plan or start date the end date, as the API does,
   until the admin types one in. Only what changed is sent. */
import { useState } from "react";

import type { Subscription } from "@/api/gen/model";
import { useOffersRetrieve } from "@/api/gen/offers/offers";
import { usePlansRetrieve } from "@/api/gen/plans/plans";
import { ErrorText, Field, Sheet } from "@/components/ui";
import { discount, offerApplies, planLength, useSoldAt } from "@/features/sell";
import { planEnd, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

export function EditMembershipSheet({ sub, branch, onClose }: { sub: Subscription; branch: number | null; onClose: () => void }) {
  const { plans, offers } = useSoldAt(branch);
  const monthDays = useSession().role.month_days;
  // The plan and offer it was sold with, even when they're no longer on sale or running.
  const soldPlan = usePlansRetrieve(sub.plan).data?.data;
  const soldOffer = useOffersRetrieve(sub.offer ?? 0, { query: { enabled: !!sub.offer } }).data?.data;
  const [plan, setPlan] = useState(sub.plan);
  const [offer, setOffer] = useState<number | null>(sub.offer ?? null);
  // Both always come back; they're optional in the type only because a sale may leave them out.
  const soldStarts = sub.starts!;
  const [starts, setStarts] = useState(soldStarts);
  const [ends, setEnds] = useState<string | null>(null); // null: worked out, not typed in
  const [price, setPrice] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();

  const onSale = plans.data?.data.results ?? [];
  const planList = soldPlan && !onSale.some((p) => p.id === soldPlan.id) ? [soldPlan, ...onSale] : onSale;
  const chosen = planList.find((p) => p.id === plan);
  const running = offers.data?.data.results ?? [];
  const offerList = (soldOffer && !running.some((o) => o.id === soldOffer.id) ? [soldOffer, ...running] : running).filter((o) => offerApplies(o, chosen));
  const chosenOffer = offerList.find((o) => o.id === offer);

  const newPlan = plan !== sub.plan;
  const newOffer = offer !== (sub.offer ?? null);
  const autoEnds = (newPlan || starts !== soldStarts) && chosen ? planEnd(starts, chosen.months, monthDays) : sub.ends!;
  const listPrice = newPlan && chosen ? chosen.price_paise : sub.list_price_paise;
  const autoPrice = newPlan || newOffer ? listPrice - discount(chosenOffer, listPrice) : sub.price_paise;

  async function save() {
    if (!reason.trim()) return setErr("Say why, for the record");
    const body = {
      reason: reason.trim(),
      ...(newPlan ? { plan } : {}),
      ...(newOffer ? { offer } : {}),
      ...(starts !== soldStarts ? { starts } : {}),
      ...(ends !== null && ends !== autoEnds ? { ends } : {}),
      ...(price !== null && toPaise(price) !== autoPrice ? { price_paise: toPaise(price) } : {}),
    };
    try { await a.run(`/api/subscriptions/${sub.id}/correct/`, body); onClose(); } catch { /* shown */ }
  }

  return (
    <Sheet open onClose={onClose} title="Edit Membership">
      <div className="rl-form">
        <Field label="Plan" error={fieldError(a.error, "plan")}>{(id) => (
          <select className="rl-field__input" id={id} value={plan}
            onChange={(e) => {
              const p = Number(e.target.value);
              setPlan(p);
              setPrice(null);
              if (chosenOffer && !offerApplies(chosenOffer, planList.find((x) => x.id === p))) setOffer(null); // an offer for other plans goes
            }}>
            {planList.map((p) => <option key={p.id} value={p.id}>{p.name} • {planLength(p)} • {rupees(p.price_paise)}{p.on_sale ? "" : " (not on sale)"}</option>)}
          </select>
        )}</Field>
        <Field label="Offer" optional error={fieldError(a.error, "offer")}>{(id) => (
          <select className="rl-field__input" id={id} value={offer ?? ""} onChange={(e) => { setOffer(e.target.value ? Number(e.target.value) : null); setPrice(null); }}>
            <option value="">No offer</option>
            {offerList.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        )}</Field>
        <div className="rl-pair">
          <Field label="Starts" error={fieldError(a.error, "starts")}>{(id) => (
            <input className="rl-field__input" id={id} type="date" value={starts} onChange={(e) => e.target.value && setStarts(e.target.value)} />
          )}</Field>
          <Field label="Ends" error={fieldError(a.error, "ends")}>{(id) => (
            <input className="rl-field__input" id={id} type="date" min={starts} value={ends ?? autoEnds} onChange={(e) => e.target.value && setEnds(e.target.value)} />
          )}</Field>
        </div>
        <Field label="Price" prefix="₹" error={fieldError(a.error, "price_paise")}
          hint={`${rupees(sub.paid_paise)} paid so far, so the price can't go below that.${newPlan || newOffer ? " Worked out from the plan and offer." : ""}`}>{(id) => (
          <input className="rl-field__input" id={id} type="number" inputMode="numeric" min={0} value={price ?? String(autoPrice / 100)} onChange={(e) => setPrice(e.target.value)} />
        )}</Field>
        <Field label="Reason" error={err ?? fieldError(a.error, "reason")} hint="Kept in the audit log with the change.">{(id) => (
          <input className="rl-field__input" id={id} value={reason} placeholder="Sold the wrong plan" onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />
        )}</Field>
      </div>
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Changes"}</button>
      </div>
    </Sheet>
  );
}
