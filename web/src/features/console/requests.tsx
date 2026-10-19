"use client";
/* Gyms asking for room for more branches: a row for the lists, and the sheet to Approve or Decline one. */
import { Building2, CalendarDays, MessageSquare, Receipt, UserRound } from "lucide-react";
import { useState } from "react";

import type { ConsoleBranchAsk } from "@/api/gen/model";
import { Details, ErrorText, Field, Photo, Sheet } from "@/components/ui";
import { AskStatus, proRataText } from "@/features/dumbelo-plan";
import { branchesOf, day, plural, rupees } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

const REFRESH = ["/api/platform/"];

const more = (n: number) => plural(n, "more branch", "more branches");

/** One request in a list. `showGym` for the list across gyms; a gym's own screen leaves its name out. */
export function RequestRow({ r, showGym, onOpen }: { r: ConsoleBranchAsk; showGym?: boolean; onOpen: () => void }) {
  return (
    <li><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={onOpen}>
      <Photo name={r.gym_name} />
      <span className="rl-row__title rl-mrow__name">{showGym ? r.gym_name : more(r.count)}</span>
      <span className="rl-row__meta rl-mrow__meta">{showGym ? `${more(r.count)} • ` : ""}Asked {day(r.created_at)} by {r.asked_by_name}</span>
      <AskStatus status={r.status} />
    </button></li>
  );
}

/** The request with the gym's plan as it is now. Approving raises the quota at once and keeps the pro-rata charge
 *  for the next invoice; declining needs a reason, which the gym's admins see. */
export function RequestSheet({ r, onClose }: { r: ConsoleBranchAsk | null; onClose: () => void }) {
  const [declining, setDeclining] = useState(false);
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const close = () => { setDeclining(false); setReason(""); setErr(undefined); a.clearError(); onClose(); };
  async function approve() {
    try { await a.run(`/api/platform/branch-requests/${r!.id}/approve/`, undefined, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  async function decline() {
    if (!reason.trim()) return setErr("Say why, so the gym's admin knows");
    try { await a.run(`/api/platform/branch-requests/${r!.id}/decline/`, { reason: reason.trim() }, { refresh: REFRESH }); close(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!r} onClose={close} title={r ? `${r.gym_name}: ${more(r.count)}` : undefined}>
      {r && (
        <>
          <Details rows={[
            { icon: UserRound, label: "Asked by", value: `${r.asked_by_name}, ${day(r.created_at)}` },
            ...(r.note ? [{ icon: MessageSquare, label: "Their note", value: r.note }] : []),
            { icon: Building2, label: "Their plan now", value: `${branchesOf(r.branches_in_use, r.branch_quota)} open` },
            r.status === "approved"
              ? { icon: Receipt, label: `Approved by ${r.decided_by_name ?? "Dumbelo"}`, value: proRataText(r) }
              : r.status === "declined"
                ? { icon: CalendarDays, label: `Declined by ${r.decided_by_name ?? "Dumbelo"}, ${day(r.decided_at ?? r.created_at)}`, value: r.decline_reason }
                : { icon: Receipt, label: "What it adds", value: `${rupees(r.per_branch_paise * r.count)} a month, and the rest of this billing month by the day on the next invoice` },
          ]} />
          {r.status === "asked" && !declining && (
            <>
              <p className="rl-row__meta">Their plan goes to room for {plural(r.branch_quota + r.count, "branch", "branches")} at once, and they can open it straight away.</p>
              <ErrorText>{a.error?.message}</ErrorText>
              <div className="rl-sheet__actions">
                <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={approve}>{a.busy ? "Approving…" : "Approve"}</button>
                <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => { a.clearError(); setDeclining(true); }}>Decline</button>
              </div>
            </>
          )}
          {r.status === "asked" && declining && (
            <form className="rl-form" noValidate style={{ marginTop: "var(--space-4)" }} onSubmit={(e) => { e.preventDefault(); decline(); }}>
              <Field label="Why" error={err ?? fieldError(a.error, "reason")} hint="The gym's admins see this on their Dumbelo plan.">
                {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={reason} maxLength={200} placeholder="Settle the October invoice first" autoFocus onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}
              </Field>
              <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
              <div className="rl-sheet__actions">
                <button className="rl-button rl-button--danger rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Declining…" : "Decline Request"}</button>
                <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setDeclining(false)}>Back</button>
              </div>
            </form>
          )}
        </>
      )}
    </Sheet>
  );
}
