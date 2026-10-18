"use client";
import { Building2 } from "lucide-react";
import Link from "next/link";

import { useReportsMembersRetrieve } from "@/api/gen/reports/reports";
import type { MembersReport as MembersData } from "@/api/gen/model";
import { Icon, Section } from "@/components/ui";
import { dayShort, plural, rangeLabel, STATUS_LABEL, trend } from "@/lib/format";
import { membersRows } from "@/lib/report-rows";

import { BarList, Lead, SeriesChart } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

const STATUSES = ["active", "expiring", "due", "frozen", "expired", "none"] as const;

/** Members: new, renewals, plans that ran out unrenewed, statuses on the last day, by branch. */
export function MembersReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsMembersRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  const rows = (d: MembersData) => membersRows(d, d.to);
  if (print) return <ReportPrint r={r} slug="members" q={q} rows={rows} />;
  return (
    <ReportScreen r={r} slug="members" q={q} rows={rows} empty={{
      when: (d) => !d.statuses.total && !d.totals.new,
      title: "No members yet", text: "Members added at the desk, their renewals and plans that run out show here.",
      action: <Link className="rl-button rl-button--secondary" href="/members/new">Add Member</Link>,
    }}>
      {(d) => <Sections d={d} today={r.today} />}
    </ReportScreen>
  );
}

function Sections({ d, today }: { d: MembersData; today: string }) {
  const range = rangeLabel(d.from, d.to);
  const t = d.totals;
  const on = dayShort(d.to);
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Lead title="New members" value={t.new.toLocaleString("en-IN")} label={`Joined, ${range}`} change={trend(t.new, d.before.new, d.days)}>
          <SeriesChart series={d.series} label={`New members, ${range}`} value={(x) => x.new} text={(n) => plural(n, "new member")} today={today} />
          <dl className="rl-facts">
            <dt>Renewals</dt><dd>{t.renewals.toLocaleString("en-IN")}</dd>
            <dt>Plans ran out, not renewed</dt><dd>{t.lapsed.toLocaleString("en-IN")}</dd>
          </dl>
        </Lead>
      </div>
      <div className="rl-app__col">
        <Section title={`Status on ${on}`} aside={<Link className="rl-link" href="/members"><span>View members</span></Link>}>
          <div className="rl-card rl-card--pad">
            <BarList rows={STATUSES.map((s) => ({ key: s, label: STATUS_LABEL[s]!, value: d.statuses[s], text: d.statuses[s].toLocaleString("en-IN") }))} />
            <dl className="rl-facts"><dt>All members</dt><dd>{d.statuses.total.toLocaleString("en-IN")}</dd></dl>
          </div>
        </Section>
        {d.branches.length > 1 && (
          <Section title="By branch">
            <ul className="rl-card rl-activity">
              {d.branches.map((b) => (
                <li key={b.id}><div className="rl-activity__row">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Building2} size="sm" /></span>
                  <span className="rl-activity__text">
                    <span className="rl-row__title">{b.name}</span>
                    <span className="rl-row__meta">{plural(b.new, "new member")} • {plural(b.renewals, "renewal")}</span>
                  </span>
                  <span className="rl-activity__amount">{b.active.toLocaleString("en-IN")} active</span>
                </div></li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}
