"use client";
import { Wallet } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { usePaymentsListInfinite } from "@/api/gen/payments/payments";
import { PageBar } from "@/components/shell";
import { Empty, LoadMore, Photo, Section, SkeletonRows, Stat } from "@/components/ui";
import { isoDate, rupees } from "@/lib/format";
import { paged, pages, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Collection } from "@/lib/types";

const METHOD = { upi: "UPI", cash: "Cash", card: "Card", bank: "Bank transfer" } as Record<string, string>;

export default function CollectionPage() {
  const { branch, branchName } = useSession();
  const [date, setDate] = useState(isoDate(new Date()));
  const col = useGet<Collection>("/api/payments/collection/", { date, branch });
  const list = usePaymentsListInfinite({ date, voided: false, ...(branch ? { branch } : {}) }, { query: paged });
  const { rows } = pages(list);
  return (
    <div className="rl-app rl-root">
      <PageBar title="Collection" sub={branchName} back="/more" />
      <main className="rl-app__main">
        <div className="rl-field" style={{ marginTop: "var(--space-2)" }}>
          <label className="rl-field__label" htmlFor="col-date">Day</label>
          <div className="rl-field__control"><input className="rl-field__input" id="col-date" type="date" max={isoDate(new Date())} value={date} onChange={(e) => setDate(e.target.value)} /></div>
        </div>
        <Section label="Totals">
          <div className="rl-kpis rl-kpis--pair">
            <Stat icon={Wallet} value={col.data ? rupees(col.data.total_paise) : "–"} label="Collected" note={col.data ? `${col.data.count} payments` : undefined} />
            <Stat icon={Wallet} value={col.data ? rupees(col.data.by_method.cash ?? 0) : "–"} label="In cash" note="To hand over" />
          </div>
          {col.data && (
            <ul className="rl-card rl-barlist" style={{ marginTop: "var(--space-3)", padding: "var(--space-3) var(--space-4)", listStyle: "none" }}>
              {Object.entries(col.data.by_method).map(([m, v]) => (
                <li key={m} style={{ display: "flex", justifyContent: "space-between", padding: "var(--space-1) 0" }}><span>{METHOD[m] ?? m}</span><strong>{rupees(v)}</strong></li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Payments">
          {list.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((p) => (
                <li key={p.id}><Link className="rl-mrow" href={`/members/${p.member}`}>
                  <Photo name={p.member_name} />
                  <span className="rl-row__title rl-mrow__name">{p.member_name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{METHOD[p.method]} • {p.taken_by_name}</span>
                  <span className="rl-mrow__time">{rupees(p.amount_paise)}</span>
                </Link></li>
              ))}
            </ul>
            <LoadMore q={list} /></>
          ) : <Empty icon={Wallet} title="No payments this day" text="Payments taken at the desk show up here." />}
        </Section>
      </main>
    </div>
  );
}
