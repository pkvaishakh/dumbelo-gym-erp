"use client";
import { AlertCircle, FileText, MessageCircle, Plus } from "lucide-react";
import { useState } from "react";

import { useBillingInvoicesListInfinite, useBillingPlanRetrieve } from "@/api/gen/billing/billing";
import type { BranchAsk, GymPlan } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Confirm, Details, Empty, ErrorText, Field, Icon, LoadMore, Section, Seg, Sheet, SkeletonRows } from "@/components/ui";
import { InvoiceRowLink } from "@/features/rackline-invoices";
import { AskStatus, BranchRoom, PlanCard, PlanPrices, proRataText } from "@/features/rackline-plan";
import { day, ordinal, plural, rupees, WHATSAPP_MODE } from "@/lib/format";
import { fieldError, paged, pages, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

const COUNTS = ["1", "2", "3", "4", "5"] as const;

/** What the gym pays Rackline, for its admins. Open while the gym is paused, so they can see what to settle. */
export default function RacklinePlanPage() {
  const { paused } = useSession();
  const q = useBillingPlanRetrieve();
  const plan = q.data?.data;
  const [asking, setAsking] = useState(false);
  return (
    <div className="rl-app rl-root">
      <PageBar title="Rackline plan" sub="What your gym pays Rackline" back="/more" />
      <main className="rl-app__main">
        {q.isError ? (
          <Empty icon={AlertCircle} title="Can't load your Rackline plan" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
          </Empty>
        ) : !plan ? <SkeletonRows n={4} /> : (
          <>
            <PlanCard plan={plan} />
            <Invoices owed={plan.owed_paise} />
            <Section title="Branches">
              <BranchRoom plan={plan} />
              <LastRequest r={plan.last_request} />
              {!paused && plan.last_request?.status !== "asked" && (
                <button className="rl-button rl-button--block" type="button" aria-haspopup="dialog" style={{ marginTop: "var(--space-3)" }} onClick={() => setAsking(true)}>
                  <Icon as={Plus} />Add Branch to My Plan
                </button>
              )}
            </Section>
            <Section title="Prices">
              <PlanPrices plan={plan} />
              <p className="rl-field__hint">
                Each month is the base fee plus the per-branch fee for every branch your plan has room for, open or not,
                billed on the {ordinal(plan.billing_day)} for the month ahead. A branch added during the month is charged
                from the day it&apos;s added.
              </p>
            </Section>
            <Section title="WhatsApp">
              <Details rows={[{ icon: MessageCircle, label: "Messages to members", value: WHATSAPP_MODE[plan.whatsapp_mode]?.note ?? plan.whatsapp_mode }]} />
            </Section>
          </>
        )}
      </main>
      {plan && <AskSheet plan={plan} open={asking} onClose={() => setAsking(false)} />}
    </div>
  );
}

/** The gym's Rackline invoices, newest first, and what's still to pay on them. Each opens with its receipts. */
function Invoices({ owed }: { owed: number }) {
  const q = useBillingInvoicesListInfinite({}, { query: paged });
  const { rows } = pages(q);
  return (
    <Section title="Invoices" aside={<p className="rl-section__aside">{owed ? `${rupees(owed)} to pay` : "Nothing to pay"}</p>}>
      {owed > 0 && (
        <p className="rl-field__hint" style={{ marginTop: 0 }}>Pay Rackline by bank transfer or UPI. Rackline records it here and you get a receipt.</p>
      )}
      {q.isLoading ? <SkeletonRows n={2} /> : q.isError ? (
        <Empty icon={AlertCircle} title="Can't load your invoices" text="Check your connection and try again.">
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      ) : rows.length ? (
        <>
          <ul className="rl-card rl-mlist rl-mlist--compact">{rows.map((inv) => <InvoiceRowLink key={inv.id} inv={inv} href={`/rackline-plan/invoices/${inv.id}`} />)}</ul>
          <LoadMore q={q} />
        </>
      ) : (
        <Empty icon={FileText} title="No invoices yet" text="Your first invoice is written on your billing day, for the month ahead." />
      )}
    </Section>
  );
}

function LastRequest({ r }: { r: BranchAsk | null }) {
  if (!r) return null;
  const more = plural(r.count, "more branch", "more branches");
  const text = r.status === "asked"
    ? `You asked for ${more} on ${day(r.created_at)}. Rackline will answer soon.`
    : r.status === "approved"
      ? `Rackline added room for ${more} on ${day(r.decided_at ?? r.created_at)}. ${proRataText(r)}.`
      : `Rackline didn't add ${more}: ${r.decline_reason}`;
  return (
    <div className="rl-card rl-card--pad" style={{ marginTop: "var(--space-3)" }}>
      <p className="rl-row__title" style={{ margin: 0, display: "flex", justifyContent: "space-between", gap: "var(--space-2)" }}>
        <span>Your last request</span><AskStatus status={r.status} />
      </p>
      <p className="rl-row__meta" style={{ marginBottom: 0 }}>{text}</p>
    </div>
  );
}

/** Add Branch to My Plan: how many more, and a note for Rackline. Rackline approves it; nothing changes until then. */
function AskSheet({ plan, open, onClose }: { plan: GymPlan; open: boolean; onClose: () => void }) {
  const [count, setCount] = useState<(typeof COUNTS)[number]>("1");
  const [note, setNote] = useState("");
  const [sent, setSent] = useState<BranchAsk | null>(null);
  const a = useAction();
  const n = Number(count);
  const close = () => { setCount("1"); setNote(""); setSent(null); a.clearError(); onClose(); };
  async function send() {
    try { setSent((await a.run<BranchAsk>("/api/billing/branch-requests/", { count: n, note: note.trim() }, { refresh: ["/api/billing/"] }))!); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={sent ? undefined : "Add Branch to My Plan"}>
      {sent ? (
        <>
          <Confirm title="Request sent" text={`Rackline will add room for ${plural(sent.count, "more branch", "more branches")} and tell you here. You can open it as soon as it's approved.`} />
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); send(); }}>
          <fieldset className="rl-fieldset"><legend>How many more branches</legend>
            <Seg label="How many more branches" value={count} onChange={setCount} options={COUNTS.map((c) => ({ value: c, label: c }))} />
          </fieldset>
          <Field label="Note for Rackline" optional error={fieldError(a.error, "note")} hint="Where it opens, or when.">
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={note} maxLength={200} placeholder="Opening in Kakkanad in December" onChange={(e) => setNote(e.target.value)} />}
          </Field>
          <p className="rl-row__meta" style={{ margin: 0 }}>
            Your plan goes to room for {plural(plan.branch_quota + n, "branch", "branches")}: {rupees(plan.per_branch_paise * n)} more a month.
            The rest of the month you&apos;re approved in is charged by the day on your next invoice.
          </p>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Sending…" : "Ask Rackline"}</button></div>
        </form>
      )}
    </Sheet>
  );
}
