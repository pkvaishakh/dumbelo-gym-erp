"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useMembersRetrieve } from "@/api/gen/members/members";
import type { Member, Subscription } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Confirm, ErrorText, Sheet } from "@/components/ui";
import { ActionBar, MemberCard, MemberPicker, PlanPicker, usePriceOf } from "@/features/sell";
import { day, rupees } from "@/lib/format";
import { useAction } from "@/lib/hooks";

function NewSubscription() {
  const params = useSearchParams();
  const router = useRouter();
  const pre = Number(params.get("member")) || 0;
  const preQ = useMembersRetrieve(pre, { query: { enabled: !!pre } });
  const [picked, setPicked] = useState<Member | null>(null);
  const member = picked ?? (preQ.data?.data as Member | undefined) ?? null;
  const [plan, setPlan] = useState<number | null>(null);
  const [offer, setOffer] = useState<number | null>(null);
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<Subscription | null>(null);
  const price = usePriceOf(plan, offer);
  const a = useAction();

  async function save() {
    if (!member) return setErr("Choose the member first");
    if (!plan) return setErr("Choose a plan");
    try { setDone((await a.run<Subscription>("/api/subscriptions/", { member: member.id, plan, offer }))!); } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="New Subscription" />
      <main className="rl-app__main">
        {member ? <MemberCard m={member} onChange={pre ? undefined : () => setPicked(null)} /> : <MemberPicker onPick={(m) => { setPicked(m); setErr(undefined); }} />}
        {member && (
          <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
            <PlanPicker plan={plan} setPlan={(v) => { setPlan(v); setErr(undefined); }} offer={offer} setOffer={setOffer} />
            {price.off > 0 && <p className="rl-field__hint">{price.offer?.name}: {rupees(price.off)} off {rupees(price.list)}</p>}
            {member.plan && member.status !== "expired" && <p className="rl-field__hint">Starts the day after the current plan ends ({day(String((member.plan as { ends: string }).ends))}).</p>}
          </form>
        )}
        <ErrorText>{err ?? a.error?.message}</ErrorText>
      </main>
      <ActionBar label="Add Plan" total={price.total ? rupees(price.total) : undefined} onClick={save} busy={a.busy} />
      <Sheet open={!!done} onClose={() => router.push(`/members/${member!.id}`)} closable={false}>
        {done && member && (
          <>
            <Confirm title={`${done.plan_name} added`} text={`${day(done.starts!)} to ${day(done.ends)}. ${rupees(done.price_paise)} to pay.`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/payments/new?member=${member.id}`}>Collect {rupees(done.price_paise)}</Link>
              <Link className="rl-button rl-button--secondary rl-button--block" href={`/members/${member.id}`}>Pay Later</Link>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><NewSubscription /></Suspense>; }
