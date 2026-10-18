"use client";
/* The Console's Server screen (and Home's server card): checks and runs as badges, a job's runs in words, and its
   sheet with Run Now. */
import { CalendarClock, Clock, Cpu, Database, Layers, ListChecks, Timer, UserRound, type LucideIcon } from "lucide-react";
import { useState } from "react";

import type { JobRun, JobStatus } from "@/api/gen/model";
import { Details, ErrorText, Sheet } from "@/components/ui";
import { ago, RUN_STATE, SERVER_STATE, took } from "@/lib/format";
import { useAction } from "@/lib/hooks";

export const STATUS = "/api/platform/status/";

export const CHECK_ICON: Record<string, LucideIcon> = { database: Database, redis: Layers, worker: Cpu, beat: Timer };

/** A check's state: Up, Down, Not used here, Can't tell. */
export function StateBadge({ state }: { state: string }) {
  const s = SERVER_STATE[state] ?? { label: state, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

export function RunBadge({ state }: { state: string }) {
  const s = RUN_STATE[state] ?? { label: state, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

/** What a run did: "12 sent • 3 not sent", or that there was nothing to do. */
export const didText = (run: JobRun) => (run.did.length ? run.did.map((d) => `${d.count.toLocaleString("en-IN")} ${d.label}`).join(" • ") : "Nothing to do");

/** One line about a job: its run under way, else its last one. */
export function jobLine(j: JobStatus) {
  if (j.current) return j.current.state === "queued" ? `Waiting for the worker since ${ago(j.current.created_at)}` : `Running since ${ago(j.current.started_at ?? j.current.created_at)}`;
  const r = j.last_run;
  if (!r) return "No runs yet";
  return r.state === "failed" ? `Failed ${ago(r.finished_at!)}: ${r.error}` : `${ago(r.finished_at!)}: ${didText(r)}`;
}

/** Run Now's words for each job it can start: what happens, and why running it again is safe. */
const RUN_NOW: Record<string, string> = {
  reminders: "Lists and sends the reminders of every gym whose reminder hour it is now, and owners' invoice reminders. Nothing already sent goes again.",
  invoices: "Writes the Rackline invoice of every gym whose billing day it is, from the invoice hour on. A month already written is skipped.",
  webhook_replay: "Handles Meta's calls of the last 7 days that couldn't be handled again. Statuses only move forward, so nothing is counted twice.",
};

/** A job's last run in full, and Run Now with a confirm for the jobs that are safe to repeat. */
export function JobSheet({ job, onClose }: { job: JobStatus | null; onClose: () => void }) {
  const [confirming, setConfirming] = useState(false);
  const a = useAction();
  const close = () => { setConfirming(false); a.clearError(); onClose(); };
  async function go() {
    try { await a.run(`/api/platform/jobs/${job!.job}/run/`, undefined, { refresh: [STATUS] }); close(); } catch { /* shown */ }
  }
  const r = job?.current ?? job?.last_run;
  return (
    <Sheet open={job !== null} onClose={close} title={confirming ? `Run ${job?.label} now?` : job?.label}>
      {job && confirming ? (
        <>
          <p className="rl-row__meta">{RUN_NOW[job.job]} It goes to the worker and runs in the background; this screen shows when it finishes.</p>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Queueing…" : "Run Now"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setConfirming(false); a.clearError(); }}>Cancel</button>
          </div>
        </>
      ) : job && (
        <>
          <Details rows={[
            { icon: CalendarClock, label: "Runs", value: job.schedule },
            ...(r ? [
              { icon: Clock, label: r.finished_at ? "Last run" : "This run", value: <><RunBadge state={r.state} /> {ago(r.started_at ?? r.created_at)}{r.seconds !== null ? `, took ${took(r.seconds)}` : ""}</> },
              { icon: UserRound, label: "Started by", value: r.trigger === "run_now" && r.by_name ? `${r.by_name}, with Run Now` : r.trigger_label },
              ...(r.finished_at ? [{ icon: ListChecks, label: "What it did", value: r.error || didText(r) }] : []),
            ] : [{ icon: Clock, label: "Last run", value: "No runs yet" }]),
          ]} />
          {job.can_run && (
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={job.current !== null} onClick={() => setConfirming(true)}>
                {job.current ? "Running now" : "Run Now"}
              </button>
            </div>
          )}
        </>
      )}
    </Sheet>
  );
}
