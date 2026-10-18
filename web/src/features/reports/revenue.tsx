"use client";
import { Undo2 } from "lucide-react";
import Link from "next/link";

import { useReportsRevenueRetrieve } from "@/api/gen/reports/reports";
import type { RevenueReport as Revenue } from "@/api/gen/model";
import { Icon, Section } from "@/components/ui";
import { dayShort, PAY_METHOD, plural, rangeLabel, rupees, trend } from "@/lib/format";
import { revenueRows } from "@/lib/report-rows";

import { BarList, Lead, moneyBars, SeriesChart, signedRupees } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

/** Revenue: collected less refunds, by day, plan, method and branch, the refunds, and what members owe now. */
export function RevenueReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsRevenueRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  if (print) return <ReportPrint r={r} slug="revenue" q={q} rows={revenueRows} />;
  return (
    <ReportScreen r={r} slug="revenue" q={q} rows={revenueRows} empty={{
      when: (d) => !d.totals.collected_paise && !d.totals.refunds_paise && !d.dues.total_paise,
      title: "No money taken in these days", text: "Payments and refunds recorded at the desk show here by the day they're taken.",
    }}>
      {(d) => <Sections d={d} today={r.today} />}
    </ReportScreen>
  );
}

function Sections({ d, today }: { d: Revenue; today: string }) {
  const range = rangeLabel(d.from, d.to);
  const t = d.totals;
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Lead title="Revenue" value={signedRupees(t.revenue_paise)} label={`Collected less refunds, ${range}`} change={trend(t.revenue_paise, d.before.revenue_paise, d.days)}>
          <SeriesChart series={d.series} label={`Revenue, ${range}`} value={(x) => x.revenue_paise} text={signedRupees} money today={today} />
          <dl className="rl-facts">
            <dt>Collected</dt><dd>{rupees(t.collected_paise)}</dd>
            <dt>Refunded{t.refunds ? `, ${plural(t.refunds, "refund")}` : ""}</dt><dd>{t.refunds_paise ? `−${rupees(t.refunds_paise)}` : rupees(0)}</dd>
          </dl>
        </Lead>
        <Section title="Owed now" aside={d.dues.members > 0 ? <Link className="rl-link" href="/members?status=due"><span>View members</span></Link> : undefined}>
          <div className="rl-card rl-card--pad">
            <dl className="rl-facts">
              <dt>Members with payment due</dt><dd>{d.dues.members.toLocaleString("en-IN")}</dd>
              <dt>Still to collect</dt><dd>{rupees(d.dues.total_paise)}</dd>
            </dl>
          </div>
        </Section>
      </div>
      <div className="rl-app__col">
        {d.by_plan.length > 0 && <Section title="By plan"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_plan)} /></div></Section>}
        {d.by_method.length > 0 && <Section title="By method"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_method)} /></div></Section>}
        {d.by_branch.length > 1 && <Section title="By branch"><div className="rl-card rl-card--pad"><BarList rows={moneyBars(d.by_branch)} /></div></Section>}
        {d.refund_list.length > 0 && (
          <Section title="Refunds">
            <ul className="rl-card rl-activity">
              {d.refund_list.map((x) => (
                <li key={x.id}><Link className="rl-activity__row" href={`/members/${x.member}`}>
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Undo2} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{x.member_name}</span>
                    <span className="rl-row__meta">{dayShort(x.on)} • {x.plan} • {PAY_METHOD[x.method]}</span>
                  </span>
                  <span className="rl-activity__amount">−{rupees(x.amount_paise)}</span>
                </Link></li>
              ))}
            </ul>
            {t.refunds > d.refund_list.length && <p className="rl-field__hint">The latest {d.refund_list.length} of {t.refunds}.</p>}
          </Section>
        )}
      </div>
    </div>
  );
}
