"use client";
import { Banknote } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useCashList } from "@/api/gen/cash/cash";
import type { DrawerClose } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Empty, ErrorText, Section, SkeletonRows, Stat } from "@/components/ui";
import { CountRow, CountSheet } from "@/features/drawer";
import { rupees } from "@/lib/format";
import { useSession } from "@/lib/session";

/** The desk's cash: each of its branches' drawers, what they should hold, today's in and out, and today's count.
 *  Read-only: only the cash, never the bank (a shared account would show other branches' takings). */
export default function CashPage() {
  const { role, branchName } = useSession();
  const q = useCashList();
  const rows = q.data?.data ?? [];
  const [open, setOpen] = useState<DrawerClose | null>(null);
  return (
    <div className="rl-app rl-root">
      <PageBar title="Cash in hand" sub={branchName} back="/more" />
      <main className="rl-app__main">
        {q.isLoading ? <SkeletonRows n={3} /> : q.isError ? (
          <ErrorText>Your branch&apos;s cash couldn&apos;t be loaded. Check your connection and try again.</ErrorText>
        ) : !rows.length ? (
          <Empty icon={Banknote} title="No branch yet" text="You aren't working at a branch yet. Ask an admin to add you to one." />
        ) : rows.map((r) => (
          <Section key={r.branch} title={r.branch_name}>
            {r.balance_paise === null ? (
              <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>{r.branch_name}&apos;s cash isn&apos;t set up yet. Ask an admin to set it up in Cash and bank.</p></div>
            ) : (
              <>
                <Stat icon={Banknote} accent value={rupees(r.balance_paise)} label="Should be in the drawer" note={`+${rupees(r.in_paise)} in, −${rupees(r.out_paise)} out today`} />
                {r.close ? (
                  <ul className="rl-card rl-activity" style={{ marginTop: "var(--space-3)" }}><CountRow c={r.close} onOpen={() => setOpen(r.close)} /></ul>
                ) : <p className="rl-field__hint">Not counted today. Count it at the end of the day.</p>}
                {!r.close?.settled_at && (
                  <Link className="rl-button rl-button--secondary rl-button--block" href={`/cash/new?branch=${r.branch}`} style={{ marginTop: "var(--space-3)" }}>
                    {r.close ? "Count Again" : "Count Cash"}
                  </Link>
                )}
              </>
            )}
          </Section>
        ))}
        <p className="rl-field__hint">Cash payments come in; cash expenses, refunds and cash banked go out. Only admins move money or settle a count that didn&apos;t match.</p>
      </main>
      {open && <CountSheet key={open.id} c={open} admin={role.role === "admin"} onClose={() => setOpen(null)} />}
    </div>
  );
}
