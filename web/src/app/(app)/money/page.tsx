"use client";
import { ArrowRightLeft, Banknote, Building2, Landmark, Wallet } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useAccountsOverviewRetrieve } from "@/api/gen/accounts/accounts";
import { useDrawerClosesList } from "@/api/gen/drawer-closes/drawer-closes";
import type { BranchMoney, DrawerClose, MoneyMove } from "@/api/gen/model";
import { useMoneyMovesListInfinite } from "@/api/gen/money-moves/money-moves";
import { PageBar } from "@/components/shell";
import { AddButton, Empty, ErrorText, Icon, LoadMore, Section, SkeletonRows, Stat, Status } from "@/components/ui";
import { CountRow, CountSheet } from "@/features/drawer";
import { accountIcon, accountMeta, BranchMoneySheet, MoveRow, MoveSheet } from "@/features/money";
import { plural, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** One branch's line: its cash, and its bank account with the branches it shares it with (counted once in the totals). */
function branchLine(b: BranchMoney) {
  const cash = b.cash ? `Cash ${rupees(b.cash.balance_paise)}` : "Cash not set up";
  if (!b.bank) return `${cash} • No bank account`;
  const shared = b.bank.shared_with.length ? `, shared with ${b.bank.shared_with.join(", ")}` : "";
  return `${cash} • ${b.bank.name} ${rupees(b.bank.balance_paise)}${shared}`;
}

export default function MoneyPage() {
  const q = useAccountsOverviewRetrieve();
  const o = q.data?.data;
  const moves = useMoneyMovesListInfinite({ limit: 10 }, { query: paged });
  const { rows, count } = pages(moves);
  const [branch, setBranch] = useState<BranchMoney | null>(null);
  const [move, setMove] = useState<MoneyMove | null>(null);
  const counts = useDrawerClosesList({ state: "to_settle", limit: 20 });
  const toSettle = counts.data?.data.results ?? [];
  const [countOpen, setCountOpen] = useState<DrawerClose | null>(null);
  const accounts = o?.accounts ?? [];
  const live = accounts.filter((a) => a.is_active);
  const off = accounts.length - live.length;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Cash and bank" sub="All branches" back="/more" action={<AddButton href="/money/move/new" label="Move Money" />} />
      <main className="rl-app__main">
        <Section label="Totals">
          <Stat icon={Wallet} accent value={o ? rupees(o.totals.total_paise) : "–"} label="Total funds" note="Each account counted once" />
          <div className="rl-kpis rl-kpis--pair" style={{ marginTop: "var(--space-3)" }}>
            <Stat icon={Banknote} value={o ? rupees(o.totals.cash_paise) : "–"} label="Cash in hand" />
            <Stat icon={Landmark} value={o ? rupees(o.totals.bank_paise) : "–"} label="In the bank" />
          </div>
          {q.isError && <ErrorText>Your accounts couldn&apos;t be loaded. Check your connection and try again.</ErrorText>}
        </Section>

        <Section title="Cash counts" aside={<Link className="rl-link" href="/cash/new"><span>Count Cash</span></Link>}>
          {counts.isLoading ? <SkeletonRows n={2} /> : toSettle.length ? (
            <>
              <ul className="rl-card rl-activity">{toSettle.map((c) => <CountRow key={c.id} c={c} onOpen={() => setCountOpen(c)} />)}</ul>
              <p className="rl-field__hint">{plural(counts.data?.data.count ?? 0, "count")} to settle. Settling records the difference as a deposit or withdrawal, so the cash holds what was counted.</p>
            </>
          ) : (
            <div className="rl-card rl-card--pad">
              <p className="rl-row__meta" style={{ margin: 0 }}>Nothing to settle. When the desk&apos;s count of a drawer doesn&apos;t match, it shows here.</p>
            </div>
          )}
          {counts.isError && <ErrorText>The cash counts couldn&apos;t be loaded. Check your connection and try again.</ErrorText>}
        </Section>

        <Section title="Branches">
          {q.isLoading ? <SkeletonRows n={3} /> : (
            <ul className="rl-card rl-activity">
              {o?.branches.map((b) => (
                <li key={b.id}><button className="rl-activity__row" type="button" aria-haspopup="dialog" onClick={() => setBranch(b)}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Building2} size="sm" /></span>
                  <span className="rl-activity__text"><span className="rl-row__title">{b.name}</span><span className="rl-row__meta">{branchLine(b)}</span></span>
                </button></li>
              ))}
            </ul>
          )}
          <p className="rl-field__hint">Tap a branch to set up its cash or change the bank account its UPI, card and bank money goes into.</p>
        </Section>

        <Section title="Accounts" aside={<Link className="rl-link" href="/money/accounts/new"><span>Add Account</span></Link>}>
          {q.isLoading ? <SkeletonRows n={4} /> : accounts.length ? (
            <ul className="rl-card rl-activity">
              {[...live, ...accounts.filter((a) => !a.is_active)].map((a) => (
                <li key={a.id}><Link className="rl-activity__row" href={`/money/accounts/${a.id}`}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={accountIcon(a.kind)} size="sm" /></span>
                  <span className="rl-activity__text"><span className="rl-row__title">{a.label}</span><span className="rl-row__meta">{accountMeta(a)}</span></span>
                  <span className="rl-activity__amount">{rupees(a.balance_paise)}</span>
                  {!a.is_active && <Status status="off" />}
                </Link></li>
              ))}
            </ul>
          ) : (
            <Empty icon={Landmark} title="No accounts yet" text="Add the gym's bank accounts and each branch's cash, and see what you hold across every branch.">
              <Link className="rl-button rl-button--block" href="/money/accounts/new">Add Account</Link>
            </Empty>
          )}
          {off > 0 && <p className="rl-field__hint">{plural(off, "account")} deactivated, kept for their history.</p>}
        </Section>

        <section className="rl-section" aria-label="Money moved">
          <div className="rl-section__head"><h2 className="rl-section__title">Money moved</h2><p className="rl-section__aside">{plural(count, "move")}</p></div>
          {moves.isLoading ? <SkeletonRows n={3} /> : rows.length ? (
            <>
              <ul className="rl-card rl-activity">{rows.map((m) => <MoveRow key={m.id} m={m} onOpen={() => setMove(m)} />)}</ul>
              <LoadMore q={moves} />
            </>
          ) : (
            <Empty icon={ArrowRightLeft} title="Nothing moved yet" text="Banking the desk's cash, drawing cash, or the owner adding funds shows here. None of it counts as income or spending.">
              {live.length > 0 && <Link className="rl-button rl-button--secondary rl-button--block" href="/money/move/new">Move Money</Link>}
            </Empty>
          )}
        </section>
      </main>
      {branch && o && <BranchMoneySheet key={branch.id} branch={o.branches.find((b) => b.id === branch.id) ?? branch} accounts={accounts} onClose={() => setBranch(null)} />}
      {move && <MoveSheet key={move.id} m={move} onClose={() => setMove(null)} />}
      {countOpen && <CountSheet key={countOpen.id} c={countOpen} admin onClose={() => setCountOpen(null)} />}
    </div>
  );
}
