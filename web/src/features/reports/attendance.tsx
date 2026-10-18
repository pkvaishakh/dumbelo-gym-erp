"use client";
import { parseISO } from "date-fns";
import Link from "next/link";

import { useReportsAttendanceRetrieve } from "@/api/gen/reports/reports";
import type { AttendanceReport as AttendanceData } from "@/api/gen/model";
import { Section } from "@/components/ui";
import { plural, rangeLabel, trend } from "@/lib/format";
import { attendanceRows } from "@/lib/report-rows";

import { BarList, Bars, Lead, SeriesChart, type Bar } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

/** Attendance: check-ins by day, session and branch, members and staff apart. Check-in time only. */
export function AttendanceReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsAttendanceRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  if (print) return <ReportPrint r={r} slug="attendance" q={q} rows={attendanceRows} />;
  return (
    <ReportScreen r={r} slug="attendance" q={q} rows={attendanceRows} empty={{
      when: (d) => !d.totals.member && !d.totals.trainer && !d.totals.receptionist && !d.totals.admin,
      title: "No check-ins in these days", text: "Check-ins at the desk, the wall QR and the turnstile show here by the day.",
    }}>
      {(d) => <Sections d={d} today={r.today} />}
    </ReportScreen>
  );
}

const WEEK = [1, 2, 3, 4, 5, 6, 0]; // Monday first
const WEEKDAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/** Over two weeks or more, a typical week says more than one long row of days: each weekday's average. */
function byWeekday(d: AttendanceData): Bar[] {
  if (d.days < 14) return [];
  const rows = WEEK.map((wd) => {
    const days = d.series.filter((x) => parseISO(x.date).getDay() === wd);
    const avg = days.length ? Math.round(days.reduce((sum, x) => sum + x.member, 0) / days.length) : 0;
    return { key: String(wd), label: WEEKDAY[wd]!, value: avg, text: `${avg.toLocaleString("en-IN")} a day` };
  });
  const top = rows.reduce((b, x) => (x.value > b.value ? x : b), rows[0]!);
  return top.value > 0 ? rows.map((x) => (x === top ? { ...x, label: `${x.label} · busiest` } : x)) : [];
}

const split = (key: string, label: string, member: number, staff: number): Bar => ({ key, label, value: member, text: `${member.toLocaleString("en-IN")} · ${staff} staff` });

function Sections({ d, today }: { d: AttendanceData; today: string }) {
  const range = rangeLabel(d.from, d.to);
  const t = d.totals;
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Lead title="Check-ins" value={t.member.toLocaleString("en-IN")} label={`Member check-ins, ${range}`} change={trend(t.member, d.before.member, d.days)}
          aside={<Link className="rl-link" href="/attendance"><span>View attendance</span></Link>}>
          <SeriesChart series={d.series} label={`Member check-ins, ${range}`} value={(x) => x.member} text={(n) => plural(n, "check-in")} today={today} />
          <dl className="rl-facts">
            <dt>Trainers</dt><dd>{t.trainer.toLocaleString("en-IN")}</dd>
            <dt>Receptionists</dt><dd>{t.receptionist.toLocaleString("en-IN")}</dd>
            {t.admin > 0 && <><dt>Admins</dt><dd>{t.admin.toLocaleString("en-IN")}</dd></>}
          </dl>
          <Bars title="Average by day of the week" rows={byWeekday(d)} />
        </Lead>
      </div>
      <div className="rl-app__col">
        {d.sessions.length > 0 && (
          <Section title="By session">
            <div className="rl-card rl-card--pad">
              <BarList rows={d.sessions.map((s) => split(s.session, s.session, s.member, s.trainer + s.receptionist + s.admin))} />
              <p className="rl-field__hint" style={{ marginBottom: 0 }}>Members, then staff. A check-in between sessions counts toward the next one.</p>
            </div>
          </Section>
        )}
        {d.branches.length > 1 && (
          <Section title="By branch">
            <div className="rl-card rl-card--pad"><BarList rows={d.branches.map((b) => split(String(b.id), b.name, b.member, b.staff))} /></div>
          </Section>
        )}
      </div>
    </div>
  );
}
