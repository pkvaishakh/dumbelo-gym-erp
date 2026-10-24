"use client";
/* Pieces shared by the desk's task screens: picking a member, a plan and an offer, and the money. */
import { Banknote, CreditCard, Landmark, Smartphone } from "lucide-react";
import { useState } from "react";

import { useMembersList } from "@/api/gen/members/members";
import type { Member, Offer, Plan } from "@/api/gen/model";
import { useOffersList } from "@/api/gen/offers/offers";
import { usePlansList } from "@/api/gen/plans/plans";
import { Choices, Photo, SearchField, Status } from "@/components/ui";
import { plural, rupees } from "@/lib/format";
import { useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";

export function ActionBar({ label, total, onClick, busy, busyLabel, secondary }: {
  label: string; total?: string; onClick: () => void; busy?: boolean; busyLabel?: string; secondary?: React.ReactNode;
}) {
  return (
    <div className="rl-actionbar"><div className="rl-actionbar__in">
      {total !== undefined && <div className="rl-actionbar__sum"><span>Total</span><strong>{total}</strong></div>}
      {secondary}
      <button className="rl-button" type="button" disabled={busy} onClick={onClick}>{busy ? busyLabel ?? "Saving…" : label}</button>
    </div></div>
  );
}

export function MemberPicker({ onPick }: { onPick: (m: Member) => void }) {
  const [q, setQ] = useState("");
  const dq = useSearch(q);
  const { branch } = useSession();
  const found = useMembersList({ q: dq, limit: 8, ...(branch ? { branch } : {}) }, { query: { enabled: dq.length >= 2 } });
  return (
    <section className="rl-section">
      <div className="rl-searchbar" style={{ position: "static" }}><SearchField value={q} onChange={setQ} placeholder="Name, phone or member ID" label="Find the member" autoFocus /></div>
      {dq.length >= 2 && (
        <ul className="rl-card rl-results" style={{ marginTop: "var(--space-3)" }}>
          {(found.data?.data.results ?? []).map((m) => (
            <li key={m.id}><button className="rl-result" type="button" style={{ width: "100%", textAlign: "left", background: "none", border: 0, font: "inherit" }} onClick={() => onPick(m)}>
              <Photo name={m.name} />
              <span className="rl-result__text"><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code} • {m.balance_paise ? `${rupees(m.balance_paise)} due` : "Nothing due"}</span></span>
              <Status status={m.status} />
            </button></li>
          ))}
          {found.data && !found.data.data.results.length && <li style={{ padding: "var(--space-4)" }}><p className="rl-row__meta" style={{ margin: 0 }}>No member matches “{dq}”.</p></li>}
        </ul>
      )}
    </section>
  );
}

export function MemberCard({ m, onChange }: { m: Member; onChange?: () => void }) {
  return (
    <section className="rl-section" aria-label="Member"><div className="rl-card rl-card--pad">
      <div className="rl-idcard__who">
        <Photo name={m.name} size="lg" />
        <span style={{ flex: 1 }}><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code}</span><Status status={m.status} /></span>
        {onChange && <button className="rl-button rl-button--secondary rl-button--sm" type="button" onClick={onChange}>Change</button>}
      </div>
    </div></section>
  );
}

/** Back to the page a task was opened from (the member's page), so it isn't in the history twice; to `fallback`
 *  when there's nothing to go back to (the task was opened on its own, in a new tab). */
export function backTo(router: { back: () => void; replace: (href: string) => void }, fallback: string) {
  if (window.history.length > 1) router.back();
  else router.replace(fallback);
}

/** "3 months", or a personal training plan's "12 sessions". */
export function planLength(p: Plan) {
  if (p.kind === "pt") return `${p.sessions} sessions`;
  return plural(p.months ?? 0, "month");
}

export function offerApplies(o: Offer, plan: Plan | undefined) {
  return !!plan && (!o.plans?.length || o.plans.includes(plan.id));
}

export function discount(o: Offer | undefined, price: number) {
  if (!o) return 0;
  return o.percent_off != null ? Math.floor((price * o.percent_off) / 100) : Math.min(o.amount_off_paise ?? 0, price);
}

/** What `branch` (the member's home branch) can sell: plans and offers given to it or to every branch. */
export function useSoldAt(branch: number | null) {
  const at = branch ? { branch } : {};
  return { plans: usePlansList({ on_sale: true, limit: 100, ...at }), offers: useOffersList({ current: true, limit: 100, ...at }) };
}

export function PlanPicker({ branch, plan, setPlan, offer, setOffer }: {
  branch: number | null; plan: number | null; setPlan: (id: number) => void; offer: number | null; setOffer: (id: number | null) => void;
}) {
  const { plans, offers } = useSoldAt(branch);
  const list = plans.data?.data.results ?? [];
  const chosen = list.find((p) => p.id === plan);
  const usable = (offers.data?.data.results ?? []).filter((o) => offerApplies(o, chosen));
  return (
    <>
      <fieldset className="rl-fieldset"><legend>Plan</legend>
        <Choices name="plan" value={plan} onChange={(v) => { setPlan(v); setOffer(null); }}
          options={list.map((p) => ({ value: p.id, title: p.name, meta: [planLength(p), p.includes].filter(Boolean).join(", "), price: rupees(p.price_paise) }))} />
      </fieldset>
      {chosen && usable.length > 0 && (
        <fieldset className="rl-fieldset"><legend>Offer <span className="rl-optional">(optional)</span></legend>
          <div className="rl-chips">
            <label className="rl-chipopt"><input type="radio" name="offer" checked={offer === null} onChange={() => setOffer(null)} /><span>No offer</span></label>
            {usable.map((o) => (
              <label className="rl-chipopt" key={o.id}><input type="radio" name="offer" checked={offer === o.id} onChange={() => setOffer(o.id)} /><span>{o.name}</span></label>
            ))}
          </div>
        </fieldset>
      )}
    </>
  );
}

export function usePriceOf(branch: number | null, plan: number | null, offer: number | null) {
  const { plans, offers } = useSoldAt(branch);
  const p = plans.data?.data.results.find((x) => x.id === plan);
  const o = offers.data?.data.results.find((x) => x.id === offer);
  const list = p?.price_paise ?? 0;
  const off = discount(o, list);
  return { plan: p, offer: o, list, off, total: list - off };
}

export const METHODS = [
  { value: "upi" as const, title: "UPI", icon: Smartphone },
  { value: "cash" as const, title: "Cash", icon: Banknote },
  { value: "card" as const, title: "Card", icon: CreditCard },
  { value: "bank" as const, title: "Bank transfer", icon: Landmark },
];
export type Method = (typeof METHODS)[number]["value"];
