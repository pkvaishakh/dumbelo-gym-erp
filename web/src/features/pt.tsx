"use client";
/* Personal training on a member's profile: the sessions left and marking one given with what they worked. Its
 * details page lists the sessions; SessionSheet shows one, changes what it worked and its notes, or removes it. */
import { CalendarDays, CircleCheck, Dumbbell, Eye, MessageCircle, Pencil, Plus, StickyNote, UserRound } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { PTPlan, PTSession } from "@/api/gen/model";
import { usePtSessionsList } from "@/api/gen/pt-sessions/pt-sessions";
import { Bar, Details, ErrorText, Field, Icon, ManageButton, PassActions, Section, Sheet, Status } from "@/components/ui";
import type { ApiError } from "@/lib/api";
import { day, gymToday, plural } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { addPart, partChoices, partsLabel, ptState, sessionsUsed } from "@/lib/pt";
import { useSession } from "@/lib/session";

/** How many recent sessions the parts offered when marking come from. */
const RECENT = 10;

/** What a session changes: the plan's count, the member's status, and the lists that show them. */
const refreshFor = (member: number) => ["/api/pt-sessions/", `/api/members/${member}/`, "/api/members/", "/api/subscriptions/"];

/** What a session worked and its notes, as typed. `other` is a part typed in but not yet added. */
type Workout = { body_parts: string[]; notes: string; other: string };
const workoutOf = (s?: PTSession): Workout => ({ body_parts: [...(s?.body_parts ?? [])], notes: s?.notes ?? "", other: "" });
/** What's sent: a part typed in counts though Add wasn't tapped. */
const workoutBody = (w: Workout) => ({ body_parts: addPart(w.body_parts, w.other), notes: w.notes.trim() });

/** A session's row line: "Chest and Biceps • With Neha", and why it was removed. */
export const sessionMeta = (s: PTSession) => [
  s.body_parts.length ? partsLabel(s.body_parts) : "", s.trainer_name ? `With ${s.trainer_name}` : `Marked by ${s.marked_by_name}`, s.voided ? `Removed: ${s.void_reason}` : "",
].filter(Boolean).join(" • ");

/** The member's personal training: a pass with the sessions left, Mark Session for staff, and an eye to its details.
 *  `money` is the desk's view of what it cost; `onWhatsApp` opens the member's WhatsApp messages; `onManage` opens an
 *  admin's Edit Membership for it. */
export function PTCard({ member, pt, money, onWhatsApp, onManage }: {
  member: number; pt: PTPlan; money?: React.ReactNode; onWhatsApp?: () => void; onManage?: () => void;
}) {
  const { role } = useSession();
  const today = gymToday(role.timezone);
  const { left, over, status } = ptState(pt, today);
  const [marking, setMarking] = useState(false);
  // Parts this plan's sessions worked beyond the usual ones, offered again when marking the next.
  const recent = usePtSessionsList({ subscription: pt.id, voided: false, limit: RECENT });
  const used = (recent.data?.data.results ?? []).flatMap((s) => s.body_parts);
  const staff = role.role !== "member";
  return (
    <Section title="Personal training">
      <div className={`rl-pass${over ? " rl-pass--expired" : status === "expiring" ? " rl-pass--renew" : ""}`}>
        <div className="rl-pass__top">
          <Status status={status} /><span className="rl-pass__plan">{pt.name}</span>
          {/* A full touch target that doesn't make the header taller: the margins take back its extra height. */}
          <Link className="rl-iconbtn rl-iconbtn--plain" href={`/members/${member}/pt`} aria-label="View Details" title="View Details"
            style={{ margin: "-10px -8px -10px auto", background: "none" }}>
            <Icon as={Eye} size="sm" />
          </Link>
        </div>
        <p className="rl-figure">{left} <small>{left === 1 ? "session left" : "sessions left"}</small></p>
        <Bar used={pt.sessions_used} total={pt.sessions} label={sessionsUsed(pt)} />
        <div className="rl-pass__dates"><span>{day(pt.starts)}</span><span>{pt.ends < today ? "Ended" : "Ends"} {day(pt.ends)}</span></div>
        <div className="rl-sub">
          <span><strong>Trainer:</strong> {pt.trainer_name ?? "Not set"}</span>
          <span>{sessionsUsed(pt)}</span>
          {pt.frozen_from && <span><strong>Frozen</strong> {day(pt.frozen_from)} to {pt.frozen_until ? day(pt.frozen_until) : "further notice"}</span>}
          {money}
        </div>
        <PassActions>
          {staff && onWhatsApp && (
            <button className="rl-button rl-button--soft rl-button--sm rl-button--icon" type="button" aria-haspopup="dialog" aria-label="WhatsApp" title="WhatsApp" onClick={onWhatsApp}>
              <Icon as={MessageCircle} size="sm" />
            </button>
          )}
          {staff && !over && (
            <button className="rl-button rl-button--soft rl-button--sm" type="button" aria-haspopup="dialog" onClick={() => setMarking(true)}>
              <Icon as={CircleCheck} size="sm" />Mark Session
            </button>
          )}
          {onManage && <ManageButton label={`Manage ${pt.name}`} onClick={onManage} />}
        </PassActions>
      </div>
      <MarkSessionSheet open={marking} member={member} pt={pt} left={left} used={used} onClose={() => setMarking(false)} />
    </Section>
  );
}

/** What a session worked, picked from the usual parts and the plan's own or typed in, and notes on it. */
function WorkoutFields({ value, onChange, used, error }: { value: Workout; onChange: (w: Workout) => void; used: string[]; error: ApiError | null }) {
  // Fixed while open, and grown by the parts added, so unticking one keeps its chip.
  const [choices, setChoices] = useState(() => partChoices(used, value.body_parts));
  const shown = partChoices(choices, value.body_parts);
  const add = () => {
    setChoices(addPart(choices, value.other));
    onChange({ ...value, body_parts: addPart(value.body_parts, value.other), other: "" });
  };
  const partsError = fieldError(error, "body_parts");
  return (
    <>
      <fieldset className={`rl-fieldset${partsError ? " is-invalid" : ""}`}>
        <legend>Worked <span className="rl-optional">(optional)</span></legend>
        <div className="rl-chips">
          {shown.map((p) => (
            <label className="rl-chipopt" key={p}>
              <input type="checkbox" checked={value.body_parts.includes(p)}
                onChange={(e) => onChange({ ...value, body_parts: e.target.checked ? addPart(value.body_parts, p) : value.body_parts.filter((x) => x !== p) })} />
              <span>{p}</span>
            </label>
          ))}
        </div>
        <ErrorText>{partsError}</ErrorText>
      </fieldset>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: "var(--space-2)", alignItems: "end" }}>
        <Field label="Another part" optional>{(id) => (
          <input className="rl-field__input" id={id} value={value.other} maxLength={30} placeholder="Abs" enterKeyHint="done"
            onChange={(e) => onChange({ ...value, other: e.target.value })}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }} />
        )}</Field>
        <button className="rl-button rl-button--secondary" type="button" disabled={!value.other.trim()} onClick={add}><Icon as={Plus} size="sm" />Add</button>
      </div>
      <Field label="Notes" optional area error={fieldError(error, "notes")}>{(id) => (
        <textarea className="rl-field__input" id={id} rows={3} maxLength={500} value={value.notes} placeholder="Bench press 40 kg, 3 sets of 8"
          onChange={(e) => onChange({ ...value, notes: e.target.value })} />
      )}</Field>
    </>
  );
}

/** Mark a session given, with what they worked. Trainers mark today's; the desk and admins may pick an earlier day
 *  inside the plan. */
function MarkSessionSheet({ open, member, pt, left, used, onClose }: { open: boolean; member: number; pt: PTPlan; left: number; used: string[]; onClose: () => void }) {
  const { role } = useSession();
  const today = gymToday(role.timezone);
  const [on, setOn] = useState(today);
  const [w, setW] = useState(workoutOf);
  const a = useAction();
  const trainer = role.role === "trainer";
  const close = () => { setOn(today); setW(workoutOf()); a.clearError(); onClose(); };
  async function go() {
    try {
      await a.run("/api/pt-sessions/", { subscription: pt.id, ...workoutBody(w), ...(trainer ? {} : { local_date: on }) }, { refresh: refreshFor(member) });
      close();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Mark Session">
      <p className="rl-row__meta">{pt.name}{pt.trainer_name ? ` with ${pt.trainer_name}` : ""}. It uses 1 of the {plural(left, "session")} left.</p>
      {!trainer && (
        <Field label="Day" error={fieldError(a.error, "local_date")} hint="Missed one? Pick the day it was given.">{(id) => (
          <input className="rl-field__input" id={id} type="date" min={pt.starts} max={today < pt.ends ? today : pt.ends} value={on} onChange={(e) => e.target.value && setOn(e.target.value)} />
        )}</Field>
      )}
      {open && <WorkoutFields value={w} onChange={setW} used={used} error={a.error} />}
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Saving…" : "Mark Session"}</button>
      </div>
    </Sheet>
  );
}

/** One session: its day, trainer, what they worked and notes. Staff change what it worked and its notes, or remove
 *  one marked by mistake: it stays on record, and the plan gets the session back. */
export function SessionSheet({ session, member, today, used, staff, onChange, onClose }: {
  session: PTSession | null; member: number; today: string; used: string[]; staff: boolean;
  onChange: (s: PTSession) => void; onClose: () => void;
}) {
  const [mode, setMode] = useState<"view" | "edit" | "remove">("view");
  const [w, setW] = useState(workoutOf);
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const back = () => { setMode("view"); setReason(""); setErr(undefined); a.clearError(); };
  const close = () => { back(); onClose(); };
  const s = session;
  async function save() {
    try {
      const out = await a.run<PTSession>(`/api/pt-sessions/${s!.id}/`, workoutBody(w), { method: "PATCH", refresh: ["/api/pt-sessions/"] });
      if (out) onChange(out);
      back();
    } catch { /* shown */ }
  }
  async function remove() {
    if (!reason.trim()) return setErr("Say why, for the record");
    try { await a.run(`/api/pt-sessions/${s!.id}/void/`, { reason: reason.trim() }, { refresh: refreshFor(member) }); close(); } catch { /* shown */ }
  }
  const when = s ? (s.local_date === today ? `Today, ${day(s.local_date)}` : day(s.local_date)) : "";
  const title = mode === "edit" ? "Edit Session" : mode === "remove" ? "Remove this session?" : "Session";
  return (
    <Sheet open={!!s} onClose={close} title={title}>
      {s && mode === "view" && (
        <>
          <Details rows={[
            { icon: CalendarDays, label: "Day", value: when },
            { icon: UserRound, label: "Trainer", value: s.trainer_name ?? "Not set" },
            { icon: Dumbbell, label: "Worked", value: partsLabel(s.body_parts) },
            { icon: StickyNote, label: "Notes", value: s.notes && <span style={{ whiteSpace: "pre-line" }}>{s.notes}</span> },
          ]} />
          <p className="rl-row__meta" style={{ marginTop: "var(--space-3)" }}>
            {s.voided ? `Removed: ${s.void_reason}. It doesn't count towards the plan.` : `${s.plan_name}. Marked by ${s.marked_by_name}.`}
          </p>
          {staff && !s.voided && (
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="button" onClick={() => { setW(workoutOf(s)); setMode("edit"); }}><Icon as={Pencil} size="sm" />Edit Session</button>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setMode("remove")}>Remove Session</button>
            </div>
          )}
        </>
      )}
      {s && mode === "edit" && (
        <>
          <p className="rl-row__meta">{when}{s.trainer_name ? ` with ${s.trainer_name}` : ""}.</p>
          <WorkoutFields value={w} onChange={setW} used={used} error={a.error} />
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Changes"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={back}>Cancel</button>
          </div>
        </>
      )}
      {s && mode === "remove" && (
        <>
          <p className="rl-row__meta">{when}{s.trainer_name ? ` with ${s.trainer_name}` : ""}. It stays on record, marked removed, and the plan gets the session back.</p>
          <Field label="Reason" error={err}>{(id) => <input className="rl-field__input" id={id} value={reason} maxLength={200} placeholder="Marked for the wrong member" onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={remove}>{a.busy ? "Removing…" : "Remove Session"}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={back}>Keep Session</button>
          </div>
        </>
      )}
    </Sheet>
  );
}
