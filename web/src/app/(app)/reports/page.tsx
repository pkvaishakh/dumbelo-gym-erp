"use client";
import { CalendarCheck, HandCoins, IndianRupee, Receipt } from "lucide-react";
import { useState } from "react";

import { PageBar } from "@/components/shell";
import { Section, SkeletonRows, Stat } from "@/components/ui";
import { SessionsTable } from "@/features/homes";
import { isoDate, plural, rupees, STATUS_LABEL } from "@/lib/format";
import { useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { Summary } from "@/lib/types";

export default function ReportsPage() {
  const { branch, branchName } = useSession();
  const [date, setDate] = useState(isoDate(new Date()));
  const s = useGet<Summary>("/api/reports/summary/", { date, branch }).data;
  const statuses = s ? (["active", "expiring", "due", "frozen", "expired"] as const).map((k) => [k, s.members[k]] as const) : [];
  const max = Math.max(1, ...statuses.map(([, v]) => v));
  return (
    <div className="rl-app rl-root">
      <PageBar title="Reports" sub={branchName} />
      <main className="rl-app__main">
        <div className="rl-field" style={{ marginTop: "var(--space-2)" }}>
          <label className="rl-field__label" htmlFor="rp-date">Day</label>
          <div className="rl-field__control"><input className="rl-field__input" id="rp-date" type="date" max={isoDate(new Date())} value={date} onChange={(e) => setDate(e.target.value)} /></div>
        </div>
        {!s ? <SkeletonRows n={4} /> : (
          <>
            <Section label="Money">
              <div className="rl-kpis rl-kpis--pair">
                <Stat icon={IndianRupee} value={rupees(s.revenue.today_paise)} label="Collected that day" />
                <Stat icon={IndianRupee} value={rupees(s.revenue.month_paise)} label="Collected this month" note="To that day" />
                <Stat icon={Receipt} value={rupees(s.expenses_month_paise)} label="Spent this month" />
                <Stat icon={HandCoins} value={rupees(s.dues.total_paise)} label="Outstanding dues" note={`From ${plural(s.dues.members, "member")}`} />
              </div>
            </Section>
            <Section title="Members by status" aside={<p className="rl-section__aside">{plural(s.members.total, "member")}</p>}>
              <ul className="rl-card rl-barlist" style={{ listStyle: "none", margin: 0, padding: "var(--space-3) var(--space-4)" }}>
                {statuses.map(([k, v]) => (
                  <li key={k} style={{ padding: "var(--space-1) 0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}><span>{STATUS_LABEL[k]}</span><strong>{v}</strong></div>
                    <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: v / max, background: "var(--ink)" }} /></span>
                  </li>
                ))}
              </ul>
            </Section>
            <Section title="Check-ins" aside={<p className="rl-section__aside"><CalendarCheck className="rl-icon rl-icon--xs" aria-hidden /> {s.checkins.total}</p>}>
              <SessionsTable sessions={s.checkins.sessions} />
            </Section>
          </>
        )}
      </main>
    </div>
  );
}
