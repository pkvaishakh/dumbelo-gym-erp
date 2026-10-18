"use client";
import { Banknote } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useCashList } from "@/api/gen/cash/cash";
import type { DrawerClose } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Chips, Confirm, Empty, ErrorText, Field, Sheet, SkeletonRows, Stat } from "@/components/ui";
import { DRAWER } from "@/features/drawer";
import { ActionBar } from "@/features/sell";
import { ago, countDifference, rupees, toPaise } from "@/lib/format";
import { useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

/** The end-of-day count: what the branch's drawer should hold, what the desk counted, and the difference. */
function CountCash() {
  const { role, branch } = useSession();
  const admin = role.role === "admin";
  const q = useCashList();
  const rows = q.data?.data ?? [];
  const asked = Number(useSearchParams().get("branch")) || branch || 0;
  const [pick, setPick] = useState(0);
  const row = rows.find((r) => r.branch === (pick || asked)) ?? rows[0];
  const [counted, setCounted] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState<DrawerClose | null>(null);
  const a = useAction();
  const paise = toPaise(counted);
  const typed = counted.trim() !== "";
  const back = admin ? "/money" : "/cash";

  async function save() {
    if (!row) return;
    if (!typed) return setErr("Enter what you counted, or 0");
    try {
      const out = await a.run<DrawerClose>("/api/drawer-closes/", { branch: row.branch, counted_paise: paise, note: note.trim() }, { refresh: DRAWER });
      setDone(out ?? null);
    } catch { /* shown */ }
  }

  const close = row?.close;
  const settled = !!close?.settled_at;
  const ready = row && row.account !== null && row.balance_paise !== null && !settled;
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Count Cash" />
      <main className="rl-app__main">
        {q.isLoading ? <SkeletonRows n={3} /> : q.isError ? (
          <ErrorText>Your branch&apos;s cash couldn&apos;t be loaded. Check your connection and try again.</ErrorText>
        ) : !row ? (
          <Empty icon={Banknote} title="No branch to count" text="You aren't working at a branch yet. Ask an admin to add you to one." />
        ) : (
          <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
            {rows.length > 1 && (
              <Chips name="count-branch" label="Branch" value={String(row.branch)} onChange={(v) => { setPick(Number(v)); setErr(undefined); a.clearError(); }}
                options={rows.map((r) => ({ value: String(r.branch), label: r.branch_name }))} />
            )}
            {row.account === null || row.balance_paise === null ? (
              <Empty icon={Banknote} title={`${row.branch_name}'s cash isn't set up`}
                text={admin ? "Count the drawer and set it up with that amount, then count it here at the end of each day." : "Ask an admin to set it up in Cash and bank, then count it here at the end of each day."}>
                {admin && <Link className="rl-button rl-button--block" href={`/money/accounts/new?kind=cash&branch=${row.branch}`}>Set Up Cash</Link>}
              </Empty>
            ) : settled ? (
              <Confirm title="Today's count is settled" text={`Counted ${rupees(close!.counted_paise)} (${countDifference(close!.difference_paise).toLowerCase()}), settled by ${close!.settled_by_name}. Ask an admin if the drawer has changed since.`} />
            ) : (
              <>
                <Stat icon={Banknote} accent value={rupees(row.balance_paise)} label={`Should be in ${row.branch_name}'s drawer`} />
                <p className="rl-field__hint" style={{ marginTop: 0 }}>From the cash payments, expenses and money moves recorded.</p>
                <fieldset className="rl-fieldset"><legend>Cash counted</legend>
                  <label className={`rl-amount${err ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
                    <input type="number" inputMode="decimal" min={0} aria-label="Cash counted in rupees" value={counted}
                      onChange={(e) => { setCounted(e.target.value); setErr(undefined); }} />
                  </label>
                  {err ? <ErrorText>{err}</ErrorText> : (
                    <p className="rl-field__hint" style={{ margin: 0 }}>{typed ? `${countDifference(paise - row.balance_paise)}: ${paise === row.balance_paise ? "nothing to settle" : "an admin settles the difference"}.` : "Count the notes and coins in the drawer."}</p>
                  )}
                </fieldset>
                <Field label="Note" optional hint="Admins read this when they settle a difference.">{(id) => (
                  <input className="rl-field__input" id={id} maxLength={200} placeholder="Gave change from my own wallet" value={note} onChange={(e) => setNote(e.target.value)} />
                )}</Field>
                {close && <p className="rl-field__hint">You counted {rupees(close.counted_paise)} {ago(close.counted_at)} ({countDifference(close.difference_paise).toLowerCase()}). Counting again replaces it.</p>}
                <ErrorText>{a.error?.message}</ErrorText>
              </>
            )}
          </form>
        )}
      </main>
      {ready ? <ActionBar label="Save Count" onClick={save} busy={a.busy} busyLabel="Saving…" /> : (
        <div className="rl-actionbar"><div className="rl-actionbar__in"><Link className="rl-button rl-button--secondary" href={back}>Done</Link></div></div>
      )}
      <Sheet open={!!done} onClose={() => {}} closable={false}>
        {done && (
          <>
            <Confirm title={done.difference_paise === 0 ? "Cash counted: it matches" : `Cash counted: ${countDifference(done.difference_paise).toLowerCase()}`}
              text={done.difference_paise === 0
                ? `${rupees(done.counted_paise)} in ${done.branch_name}'s drawer, as expected. Nothing to settle.`
                : `${rupees(done.counted_paise)} counted against ${rupees(done.expected_paise)} expected. An admin settles the difference; until then you can count again today.`} />
            <div className="rl-sheet__actions"><Link className="rl-button rl-button--block" href={back}>Done</Link></div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><CountCash /></Suspense>; }
