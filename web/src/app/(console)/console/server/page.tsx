"use client";
import type { LucideIcon } from "lucide-react";
import { AlertCircle, CalendarClock, Cpu, Database, FileText, Layers, MessageCircle, RefreshCw, RotateCw, Send, Timer, Webhook } from "lucide-react";
import { useState } from "react";

import type { JobStatus, ServerStatus } from "@/api/gen/model";
import { usePlatformStatusRetrieve } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Details, Empty, Icon, Section, SkeletonRows } from "@/components/ui";
import { jobLine, JobSheet, RunBadge } from "@/features/console/server";
import { ago, plural, SERVER_STATE } from "@/lib/format";

const CHECK_ICON: Record<string, LucideIcon> = { database: Database, redis: Layers, worker: Cpu, beat: Timer };
const JOB_ICON: Record<string, LucideIcon> = { reminders: Send, invoices: FileText, retries: RotateCw, webhook_replay: Webhook };

function StateBadge({ state }: { state: string }) {
  const s = SERVER_STATE[state] ?? { label: state, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

/** While a run waits or runs, check every few seconds so its end shows; otherwise every half minute. */
const every = (s: ServerStatus | undefined) => (s?.jobs?.some((j) => j.current) ? 3_000 : 30_000);

/** Console → Server: whether the API, database, Redis, the worker and beat are answering; each job's last run,
 *  with Run Now for the safe-to-repeat ones; messages waiting or failed; and Meta's webhook calls. */
export default function Server() {
  const q = usePlatformStatusRetrieve({ query: { refetchInterval: (query) => every(query.state.data?.data) } });
  const s = q.data?.data;
  const [open, setOpen] = useState<string | null>(null);
  const job = s?.jobs?.find((j) => j.job === open) ?? null; // read fresh from each check, so the sheet follows the run
  const sub = s ? `Version ${s.version}${s.deployed_at ? ` • deployed ${ago(s.deployed_at)}` : ""}` : "Health, jobs and messages";
  return (
    <div className="rl-app rl-root">
      <PageBar title="Server" sub={sub} action={
        <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Check again" disabled={q.isFetching} onClick={() => q.refetch()}><Icon as={RefreshCw} /></button>
      } />
      <main className="rl-app__main">
        {q.isLoading ? <SkeletonRows n={4} /> : q.isError || !s ? (
          <Empty icon={AlertCircle} title="Can't reach the API" text={q.error instanceof Error ? q.error.message : "The API isn't answering, or your connection is down. Try again in a moment."}>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
          </Empty>
        ) : (
          <>
            <Section title="Health" aside={<p className="rl-section__aside">Checked {ago(s.checked_at)}</p>}>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {s.checks.map((c) => (
                  <li key={c.key}><div className="rl-mrow">
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={CHECK_ICON[c.key] ?? AlertCircle} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{c.label}</span>
                    <span className="rl-row__meta rl-mrow__meta">{c.at ? `Ticked ${ago(c.at)}` : c.detail}</span>
                    <StateBadge state={c.state} />
                  </div></li>
                ))}
              </ul>
            </Section>
            <Jobs jobs={s.jobs} onOpen={setOpen} />
            <Section title="Messages">
              {s.messages ? (
                <Details rows={[
                  { icon: RotateCw, label: "Waiting for a retry", value: s.messages.waiting_retry.toLocaleString("en-IN") },
                  { icon: AlertCircle, label: "Failed today", value: s.messages.failed_today.toLocaleString("en-IN") },
                ]} />
              ) : <Unreadable />}
            </Section>
            <Section title="Webhook" aside={s.webhook ? <p className="rl-section__aside">Last {s.webhook.failed_days} days</p> : undefined}>
              {s.webhook ? (
                <>
                  <Details rows={[{ icon: Webhook, label: "Calls that couldn't be handled", value: s.webhook.failed.toLocaleString("en-IN") }]} />
                  {s.webhook.numbers.length > 0 && (
                    <ul className="rl-card rl-mlist rl-mlist--compact" style={{ marginTop: "var(--space-3)" }}>
                      {s.webhook.numbers.map((n) => (
                        <li key={n.id}><div className="rl-mrow">
                          <span className="rl-chipicon" aria-hidden="true"><Icon as={MessageCircle} size="sm" /></span>
                          <span className="rl-row__title rl-mrow__name">{n.display_number}</span>
                          <span className="rl-row__meta rl-mrow__meta">{n.is_shared ? "Shared" : n.gym_name} • {n.last_call_at ? `Meta last called ${ago(n.last_call_at)}` : "Meta hasn't called yet"}</span>
                        </div></li>
                      ))}
                    </ul>
                  )}
                  {s.webhook.failed > 0 && <p className="rl-row__meta">Once the cause is fixed, open Webhook replay above and Run Now to handle them again.</p>}
                </>
              ) : <Unreadable />}
            </Section>
          </>
        )}
      </main>
      <JobSheet job={job} onClose={() => setOpen(null)} />
    </div>
  );
}

function Jobs({ jobs, onOpen }: { jobs: JobStatus[] | null; onOpen: (job: string) => void }) {
  const failed = jobs?.filter((j) => !j.current && j.last_run?.state === "failed").length ?? 0;
  return (
    <Section title="Jobs" aside={failed ? <p className="rl-section__aside">{plural(failed, "failed last run", "failed last runs")}</p> : undefined}>
      {jobs ? (
        <ul className="rl-card rl-mlist rl-mlist--compact">
          {jobs.map((j) => {
            const run = j.current ?? j.last_run;
            return (
              <li key={j.job}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => onOpen(j.job)}>
                <span className="rl-chipicon" aria-hidden="true"><Icon as={JOB_ICON[j.job] ?? CalendarClock} size="sm" /></span>
                <span className="rl-row__title rl-mrow__name">{j.label}</span>
                <span className="rl-row__meta rl-mrow__meta">{jobLine(j)}</span>
                {run && <RunBadge state={run.state} />}
              </button></li>
            );
          })}
        </ul>
      ) : <Unreadable />}
    </Section>
  );
}

function Unreadable() {
  return <Empty icon={Database} title="Can't read this now" text="It comes from the database, which isn't answering. It shows again once the database is back." />;
}
