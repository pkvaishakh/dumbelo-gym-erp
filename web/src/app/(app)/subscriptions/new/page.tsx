"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { addDays, parseISO } from "date-fns";
import { CalendarCheck, CalendarClock } from "lucide-react";

import { useMembersRetrieve } from "@/api/gen/members/members";
import type { Member, Subscription } from "@/api/gen/model";
import { useSubscriptionsList } from "@/api/gen/subscriptions/subscriptions";
import { TaskBar } from "@/components/shell";
import { Confirm, ErrorText, Field, Icon, Section, Sheet } from "@/components/ui";
import { ActionBar, backTo, MemberCard, MemberPicker, PlanPicker, usePriceOf } from "@/features/sell";
import { day, gymToday, isoDate, planEnd, rupees } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

function NewSubscription() {
  const params = useSearchParams();
  const router = useRouter();
  const pre = Number(params.get("member")) || 0;
  const fromMember = params.get("back") === "member"; // opened from the member's page: finishing goes back there
  const preQ = useMembersRetrieve(pre, { query: { enabled: !!pre } });
  const [picked, setPicked] = useState<Member | null>(null);
  const member = picked ?? (preQ.data?.data as Member | undefined) ?? null;
  const [plan, setPlan] = useState<number | null>(null);
  const [offer, setOffer] = useState<number | null>(null);
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<Subscription | null>(null);
  const price = usePriceOf(member?.home_branch ?? null, plan, offer);
  const a = useAction();
  const { role } = useSession();
  const admin = role.role === "admin";
  // The plan running now and any renewals already sold: a new one starts after the last of them, as the API does.
  const subsQ = useSubscriptionsList({ member: member?.id ?? 0, limit: 5 }, { query: { enabled: !!member } });
  const today = gymToday(role.timezone);
  const lined = (subsQ.data?.data.results ?? []).filter((s) => !s.cancelled && s.ends! >= today).sort((x, y) => (x.starts ?? "").localeCompare(y.starts ?? ""));
  const last = lined.reduce<Subscription | null>((l, s) => (!l || s.ends! > l.ends! ? s : l), null);
  const nextStart = last ? isoDate(addDays(parseISO(last.ends!), 1)) : today;
  const [starts, setStarts] = useState<string | null>(null); // null: the next free day
  const [ends, setEnds] = useState<string | null>(null); // null: from the plan's length (admins may type one)
  const start = starts ?? nextStart;
  const autoEnds = price.plan ? planEnd(start, price.plan.months, role.month_days) : "";

  async function save() {
    if (!member) return setErr("Choose the member first");
    if (!plan) return setErr("Choose a plan");
    // A start left as it was is left to the API (the same day, worked out from plans this page may still be loading).
    const body = { member: member.id, plan, offer, ...(starts !== null ? { starts } : {}), ...(admin && ends !== null && ends !== autoEnds ? { starts: start, ends } : {}) };
    try { setDone((await a.run<Subscription>("/api/subscriptions/", body))!); } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="New Subscription" />
      <main className="rl-app__main">
        {member ? <MemberCard m={member} onChange={pre ? undefined : () => { setPicked(null); setPlan(null); setOffer(null); setStarts(null); setEnds(null); }} /> : <MemberPicker onPick={(m) => { setPicked(m); setErr(undefined); }} />}
        {member && lined.length > 0 && (
          <Section title="Now and up next">
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {lined.map((s) => (
                <li key={s.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={(s.starts ?? "") <= today ? CalendarCheck : CalendarClock} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{s.plan_name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{day(s.starts!)} to {day(s.ends!)}</span>
                  <span className="rl-mrow__note">{(s.starts ?? "") <= today ? "Now" : "Queued"}</span>
                </div></li>
              ))}
            </ul>
          </Section>
        )}
        {member && (
          <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
            <PlanPicker branch={member.home_branch} plan={plan} setPlan={(v) => { setPlan(v); setEnds(null); setErr(undefined); }} offer={offer} setOffer={setOffer} />
            {price.off > 0 && <p className="rl-field__hint">{price.offer?.name}: {rupees(price.off)} off {rupees(price.list)}</p>}
            <div className="rl-pair">
              <Field label="Starts" error={fieldError(a.error, "starts")}>{(id) => (
                <input className="rl-field__input" id={id} type="date" value={start} onChange={(e) => { if (e.target.value) { setStarts(e.target.value); setEnds(null); } }} />
              )}</Field>
              <Field label="Ends" error={fieldError(a.error, "ends")}>{(id) => (
                <input className="rl-field__input" id={id} type="date" min={start} readOnly={!admin} value={ends ?? autoEnds} placeholder="Pick a plan"
                  onChange={(e) => e.target.value && setEnds(e.target.value)} />
              )}</Field>
            </div>
            <p className="rl-field__hint">
              {starts === null && last ? `Starts the day after ${last.plan_name} ends (${day(last.ends!)}). ` : ""}
              {admin ? "The end date follows the plan's length unless you change it." : "The end date follows the plan's length."}
            </p>
          </form>
        )}
        <ErrorText>{err ?? a.error?.message}</ErrorText>
      </main>
      <ActionBar label="Add Plan" total={price.total ? rupees(price.total) : undefined} onClick={save} busy={a.busy} />
      <Sheet open={!!done} onClose={() => (fromMember ? backTo(router, `/members/${member!.id}`) : router.push(`/members/${member!.id}`))} closable={false}>
        {done && member && (
          <>
            <Confirm title={`${done.plan_name} added`} text={`${day(done.starts!)} to ${day(done.ends!)}. ${rupees(done.price_paise)} to pay.`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/payments/new?member=${member.id}${fromMember ? "&back=member" : ""}`} replace={fromMember}>Collect {rupees(done.price_paise)}</Link>
              {fromMember
                ? <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => backTo(router, `/members/${member.id}`)}>Pay Later</button>
                : <Link className="rl-button rl-button--secondary rl-button--block" href={`/members/${member.id}`}>Pay Later</Link>}
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><NewSubscription /></Suspense>; }
