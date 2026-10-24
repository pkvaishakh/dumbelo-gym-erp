"use client";
import { Building2, Clock } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { CheckIn } from "@/api/gen/model";
import { Confirm, Details, ErrorText, Field, Photo, Sheet } from "@/components/ui";
import { fieldError, useAction } from "@/lib/hooks";
import { gymClock } from "@/lib/format";
import { useSession } from "@/lib/session";

const ROLE = { admin: "Admin", receptionist: "Receptionist", trainer: "Trainer" } as const;

/** One check-in, opened from its row on Attendance: who, when, and for the desk Change Time and Remove Check-In.
 *  Earlier days are a record for receptionists; admins can correct any day (the API holds the same rule).
 *  Render it keyed by the check-in, so each one opens on its own first step. */
export function VisitSheet({ visit, dayLabel, isToday, onClose }: { visit: CheckIn; dayLabel: string; isToday: boolean; onClose: () => void }) {
  const { role } = useSession();
  const canFix = role.role === "admin" || (role.role === "receptionist" && isToday);
  const [step, setStep] = useState<"view" | "time" | "remove">("view");
  const [time, setTime] = useState("");
  const a = useAction();

  const close = () => { a.clearError(); onClose(); };
  const refresh = ["/api/checkins/", "/api/reports/"];
  async function saveTime() {
    try { await a.run(`/api/checkins/${visit.id}/`, { time }, { method: "PATCH", refresh }); close(); } catch { /* shown */ }
  }
  async function remove() {
    try { await a.run(`/api/checkins/${visit.id}/`, undefined, { method: "DELETE", refresh }); close(); } catch { /* shown */ }
  }

  const member = visit.kind === "member";
  const profile = member ? `/members/${visit.person_id}` : role.role === "admin" ? `/staff/${visit.person_id}` : null;  // the desk doesn't open staff profiles
  const when = `${visit.time}${isToday ? " today" : `, ${dayLabel}`}`;
  return (
    <Sheet open onClose={close} title={step === "remove" ? undefined : step === "time" ? "Change Time" : isToday ? "Today’s visit" : `Visit on ${dayLabel}`}>
      {step === "view" && (
        <>
          <div className="rl-idcard"><div className="rl-idcard__who">
            <Photo name={visit.name} size="lg" />
            <span><span className="rl-row__title">{visit.name}</span><span className="rl-row__meta">{member ? visit.code : ROLE[visit.kind as keyof typeof ROLE]}</span></span>
          </div></div>
          <Details rows={[
            { icon: Clock, label: "Checked in", value: visit.session ? `${visit.time}, ${visit.session}` : visit.time },
            { icon: Building2, label: "Branch", value: visit.branch_name },
          ]} />
          <div className="rl-sheet__actions">
            {profile && <Link className="rl-button rl-button--secondary rl-button--block" href={profile}>View Profile</Link>}
            {canFix && <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setTime(visit.at ? gymClock(visit.at, role.timezone) : ""); setStep("time"); }}>Change Time</button>}
            {canFix && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" aria-haspopup="dialog" onClick={() => setStep("remove")}>Remove Check-In</button>}
          </div>
        </>
      )}
      {step === "time" && (
        <>
          <p className="rl-row__meta">{visit.name} checked in at {when}. Use this when the time is wrong, like a turnstile clock that was off.</p>
          <Field label="Checked in at" error={fieldError(a.error, "time")} hint="Same day. The session follows the new time.">
            {(id, describedBy) => <input className="rl-field__input" id={id} type="time" value={time} aria-describedby={describedBy} onChange={(e) => setTime(e.target.value)} />}
          </Field>
          {!fieldError(a.error, "time") && <ErrorText>{a.error?.message}</ErrorText>}
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy || !time} onClick={saveTime}>{a.busy ? "Saving…" : "Save Time"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { a.clearError(); setStep("view"); }}>Cancel</button>
          </div>
        </>
      )}
      {step === "remove" && (
        <>
          <Confirm blocked title="Remove this check-in?" text={`${visit.name}, ${when}. Use this when the wrong ${member ? "member" : "person"} was checked in. This cannot be undone.`} />
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={remove}>{a.busy ? "Removing…" : "Remove Check-In"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { a.clearError(); setStep("view"); }}>Keep It</button>
          </div>
        </>
      )}
    </Sheet>
  );
}
