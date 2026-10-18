"use client";
import Link from "next/link";

import { useReportsTasksRetrieve } from "@/api/gen/reports/reports";
import type { TasksReport as TasksData } from "@/api/gen/model";
import { Photo, Section, TaskStatus } from "@/components/ui";
import { clock, day, plural, rangeLabel, trend } from "@/lib/format";
import { tasksRows } from "@/lib/report-rows";

import { Lead } from "./parts";
import type { ReportRange } from "./range";
import { ReportPrint, ReportScreen } from "./screen";

const ROLE: Record<string, string> = { trainer: "Trainer", receptionist: "Receptionist", admin: "Admin" };

/** Tasks due in the days: done, open and overdue, by person, and the oldest overdue to chase. */
export function TasksReport({ r, print }: { r: ReportRange; print?: boolean }) {
  const q = useReportsTasksRetrieve(r.api, { query: { enabled: r.isAdmin && !r.invalid } });
  if (print) return <ReportPrint r={r} slug="tasks" q={q} rows={tasksRows} />;
  return (
    <ReportScreen r={r} slug="tasks" q={q} rows={tasksRows} empty={{
      when: (d) => !d.totals.total,
      title: "No tasks due in these days", text: "Tasks you give trainers and receptionists show up here by their due date.",
      action: <Link className="rl-button rl-button--secondary" href="/tasks?new=1">New Task</Link>,
    }}>
      {(d) => <Sections d={d} />}
    </ReportScreen>
  );
}

function Sections({ d }: { d: TasksData }) {
  const t = d.totals;
  const share = t.total ? t.done / t.total : 0;
  return (
    <div className="rl-app__cols">
      <div className="rl-app__col">
        <Lead title="Tasks" value={`${t.done} of ${t.total} done`} label={`Due ${rangeLabel(d.from, d.to)}`} change={trend(t.done, d.before.done, d.days)}
          aside={<Link className="rl-link" href="/tasks?filter=all"><span>View tasks</span></Link>}>
          <span className="rl-bar" role="img" aria-label={`${Math.round(share * 100)}% done`} style={{ height: 8, marginTop: "var(--space-4)", background: "var(--surface)" }}>
            <span className="rl-bar__fill" style={{ ["--v" as string]: share }} />
          </span>
          <dl className="rl-facts">
            <dt>To do</dt><dd>{t.todo}</dd>
            <dt>In progress</dt><dd>{t.doing}</dd>
            <dt>Done</dt><dd>{t.done}</dd>
            <dt>Overdue</dt><dd style={t.overdue ? { color: "var(--attention)" } : undefined}>{t.overdue}</dd>
          </dl>
          <p className="rl-report__sub">By person</p>
          <ul className="rl-barlist">
            {d.people.map((p) => (
              <li key={p.id}>
                <div className="rl-barlist__top"><span>{p.name}</span><span>{p.done} of {p.total} done</span></div>
                <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: p.total ? p.done / p.total : 0 }} /></span>
                <p className="rl-row__meta" style={{ margin: "4px 0 0" }}>
                  {ROLE[p.role] ?? p.role}{p.overdue > 0 && <> · <span style={{ color: "var(--attention)", fontWeight: 600 }}>{plural(p.overdue, "overdue task")}</span></>}
                </p>
              </li>
            ))}
          </ul>
        </Lead>
      </div>
      <div className="rl-app__col">
        {d.late.length > 0 && (
          <Section title="Oldest overdue" aside={t.overdue > d.late.length ? <Link className="rl-link" href="/tasks?filter=overdue"><span>See all {t.overdue}</span></Link> : undefined}>
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {d.late.map((x) => (
                <li key={x.id}><Link className="rl-mrow rl-tkrow" href={`/tasks?open=${x.id}`}>
                  <Photo name={x.assignee_name} />
                  <span className="rl-row__title rl-mrow__name">{x.title}</span>
                  <span className="rl-row__meta rl-mrow__meta">{x.assignee_name} • Due {day(x.due_date)}{x.due_time ? `, ${clock(x.due_time)}` : ""}</span>
                  <TaskStatus status={x.status} overdue />
                </Link></li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}
