"use client";
import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine, Building2, Hash, Landmark, Pencil, Receipt, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useAccountsRetrieve } from "@/api/gen/accounts/accounts";
import type { MoneyMove } from "@/api/gen/model";
import { useMoneyMovesListInfinite } from "@/api/gen/money-moves/money-moves";
import { DetailBar } from "@/components/shell";
import { Details, Empty, ErrorText, Icon, LoadMore, Section, Sheet, SkeletonRows, Status } from "@/components/ui";
import { MONEY, MoveRow, MoveSheet } from "@/features/money";
import { day, plural, rupees } from "@/lib/format";
import { paged, pages, useAction } from "@/lib/hooks";

export default function AccountRecord() {
  const { id } = useParams<{ id: string }>();
  const q = useAccountsRetrieve(Number(id));
  const acct = q.data?.data;
  const moves = useMoneyMovesListInfinite({ account: Number(id), limit: 10 }, { query: paged });
  const { rows, count } = pages(moves);
  const [move, setMove] = useState<MoneyMove | null>(null);
  const [confirm, setConfirm] = useState(false);
  const a = useAction();
  if (q.isError) return <div className="rl-app rl-root"><DetailBar title="Account" back="/money" /><main className="rl-app__main"><p className="rl-row__meta">This account couldn&apos;t be found.</p></main></div>;
  if (!acct) return <div className="rl-app rl-root"><DetailBar title="Account" back="/money" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  const cash = acct.kind === "cash";
  async function toggle() {
    try {
      await a.run(`/api/accounts/${acct!.id}/${acct!.is_active ? "deactivate" : "activate"}/`, undefined, { refresh: MONEY });
      setConfirm(false);
    } catch { /* shown */ }
  }
  const signed = (n: number, sign: "+" | "−") => (n ? `${sign}${rupees(n)}` : rupees(0));
  return (
    <div className="rl-app rl-root">
      <DetailBar title={acct.label} back="/money"
        action={acct.is_active ? <Link className="rl-iconbtn rl-iconbtn--plain" href={`/money/accounts/${acct.id}/edit`} aria-label="Edit"><Icon as={Pencil} /></Link> : undefined} />
      <main className="rl-app__main">
        <section className="rl-section" aria-label="Balance"><div className="rl-pass">
          <div className="rl-pass__top"><span className="rl-pass__plan">{cash ? "Cash in hand" : acct.bank_name}</span>{!acct.is_active && <Status status="off" />}</div>
          <p className="rl-figure">{rupees(acct.balance_paise)}</p>
          <div className="rl-pass__dates"><span>Balance now</span><span>Added {day(acct.opened_on)}</span></div>
        </div></section>
        {acct.is_active && (
          <Section label="Move money">
            <Link className="rl-button rl-button--secondary rl-button--block" href={`/money/move/new?account=${acct.id}`}>Move Money</Link>
          </Section>
        )}
        <Section title="How it got here" aside={<Link className="rl-link" href={`/money/accounts/${acct.id}/statement`}><span>Statement</span></Link>}>
          <Details rows={[
            { icon: Wallet, label: "Opening balance", value: rupees(acct.opening_balance_paise) },
            { icon: ArrowDownToLine, label: "Payments taken in", value: signed(acct.collected_paise, "+") },
            { icon: Receipt, label: "Expenses paid out", value: signed(acct.spent_paise, "−") },
            { icon: ArrowRightLeft, label: "Moved in", value: signed(acct.moved_in_paise, "+") },
            { icon: ArrowUpFromLine, label: "Moved out", value: signed(acct.moved_out_paise, "−") },
          ]} />
          <p className="rl-field__hint">Payments and expenses count from the day it was added. Voided payments and moves don&apos;t count.</p>
        </Section>
        <Section title="Details">
          <Details rows={cash ? [
            { icon: Building2, label: "Branch", value: acct.branch_name },
          ] : [
            { icon: Landmark, label: "Bank", value: acct.bank_name },
            { icon: Hash, label: "Account number", value: acct.account_number },
            { icon: Hash, label: "IFSC", value: acct.ifsc },
            { icon: Building2, label: "Branches that use it", value: acct.branch_names.length ? acct.branch_names.join(", ") : "No branch" },
          ]} />
        </Section>
        <section className="rl-section" aria-label="Money moved">
          <div className="rl-section__head"><h2 className="rl-section__title">Money moved</h2><p className="rl-section__aside">{plural(count, "move")}</p></div>
          {moves.isLoading ? <SkeletonRows n={3} /> : rows.length ? (
            <>
              <ul className="rl-card rl-activity">{rows.map((m) => <MoveRow key={m.id} m={m} account={acct.id} onOpen={() => setMove(m)} />)}</ul>
              <LoadMore q={moves} />
            </>
          ) : <Empty icon={ArrowRightLeft} title="Nothing moved yet" text="Deposits, withdrawals and transfers in or out of this account show here." />}
        </section>
        <Section label={acct.is_active ? "Deactivate" : "Reactivate"}>
          {acct.is_active
            ? <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => setConfirm(true)}>Deactivate Account</button>
            : <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={toggle}>{a.busy ? "Reactivating…" : "Reactivate Account"}</button>}
          {!acct.is_active && <ErrorText>{a.error?.message}</ErrorText>}
        </Section>
      </main>
      {move && <MoveSheet key={move.id} m={move} onClose={() => setMove(null)} />}
      <Sheet open={confirm} onClose={() => { setConfirm(false); a.clearError(); }} title={`Deactivate ${acct.label}?`}>
        <p className="rl-row__meta">
          {acct.balance_paise ? `It holds ${rupees(acct.balance_paise)}. Move that to another account first, so nothing drops out of your totals. ` : "It holds nothing, so your totals don't change. "}
          {cash ? `${acct.branch_name}'s cash stops being counted.` : acct.branch_names.length ? `${acct.branch_names.join(" and ")} will have no bank account until you give them one.` : ""} Its history stays.
        </p>
        <ErrorText>{a.error?.message}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={toggle}>{a.busy ? "Deactivating…" : "Deactivate It"}</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setConfirm(false)}>Keep It</button>
        </div>
      </Sheet>
    </div>
  );
}
