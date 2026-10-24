"use client";
import { ChevronDown, Plus, QrCode, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { Branch } from "@/api/gen/model";
import { Chips, ErrorText, Field, Icon, Section } from "@/components/ui";
import { clock } from "@/lib/format";
import { useAction } from "@/lib/hooks";

import { ActionBar } from "./sell";

type Row = { name: string; starts: string; ends: string };
const DEFAULT: Row[] = [{ name: "Morning", starts: "05:00", ends: "10:00" }, { name: "Evening", starts: "17:00", ends: "22:00" }];

/** Every quarter hour of the day as a time input holds it: "00:00", "00:15" … "23:45". */
const QUARTERS = Array.from({ length: 96 }, (_, i) => `${String(Math.floor(i / 4)).padStart(2, "0")}:${String((i % 4) * 15).padStart(2, "0")}`);

/** A time of day picked on a 12-hour clock ("5:30 AM"), held as "05:30". A time saved off the quarter hour stays on offer. */
function ClockPick({ label, value, onChange, invalid }: { label: string; value: string; onChange: (t: string) => void; invalid?: boolean }) {
  const times = value && !QUARTERS.includes(value) ? [...QUARTERS, value].sort() : QUARTERS;
  return (
    <label className="rl-mini">
      <span>{label}</span>
      <span className="rl-mini__pick">
        <select className={[invalid && "is-invalid", !value && "is-empty"].filter(Boolean).join(" ") || undefined} value={value} aria-invalid={invalid || undefined} onChange={(e) => onChange(e.target.value)}>
          {!value && <option value="" disabled>Choose</option>}
          {times.map((t) => <option key={t} value={t}>{clock(t)}</option>)}
        </select>
        <Icon as={ChevronDown} size="sm" />
      </span>
    </label>
  );
}

/** What's wrong with a session, in the words shown on it, or nothing. */
function rowProblem(r: Row) {
  if (!r.name.trim() && (!r.starts || !r.ends)) return "Name this session and give it a start and end";
  if (!r.name.trim()) return "Name this session";
  if (!r.starts || !r.ends) return "Give this session a start and end";
  if (r.ends <= r.starts) return "End this session after it starts";
}

/** Add Branch / Edit Branch: details and opening hours as named sessions (Morning 5–10 AM, Evening 5–10 PM…). */
export function BranchForm({ branch, onSaved }: { branch?: Branch; onSaved: (b: Branch) => void }) {
  const [f, setF] = useState({ name: branch?.name ?? "", address: branch?.address ?? "", phone: branch?.phone ?? "", days_open: branch?.days_open ?? "every_day" });
  const [rows, setRows] = useState<Row[]>(branch ? branch.sessions.map((s) => ({ name: s.name, starts: s.starts.slice(0, 5), ends: s.ends.slice(0, 5) })) : DEFAULT);
  const [nameErr, setNameErr] = useState<string>();
  const [rowsErr, setRowsErr] = useState<string>();
  const [checked, setChecked] = useState(false); // show each session's problem once Save has been tried
  const a = useAction();
  const setRow = (i: number, k: keyof Row, v: string) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)));

  async function save(extra?: object) {
    setChecked(true);
    const noName = f.name.trim() ? undefined : "Enter the branch name";
    const noRows = rows.length ? undefined : "Add at least one session";
    setNameErr(noName);
    setRowsErr(noRows);
    if (noName || noRows || rows.some(rowProblem)) return;
    try {
      const b = await a.run<Branch>(branch ? `/api/branches/${branch.id}/` : "/api/branches/", { ...f, name: f.name.trim(), sessions: rows, ...extra }, { method: branch ? "PATCH" : "POST", refresh: ["/api/branches/", "/api/me/", "/api/billing/"] });  // opening or closing one changes the plan's room
      onSaved(b!);
    } catch { /* shown */ }
  }
  const sessionsMsg = Array.isArray(a.error?.fields?.sessions) ? String((a.error!.fields!.sessions as string[])[0]) : undefined;
  return (
    <>
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Branch name" error={nameErr} hint="Members and staff see this name.">
          {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={f.name} autoComplete="off" autoCapitalize="words" enterKeyHint="next" placeholder="For example, Jayanagar" onChange={(e) => { setF({ ...f, name: e.target.value }); setNameErr(undefined); }} />}
        </Field>
        <Field label="Address" optional area>{(id) => <textarea className="rl-field__input" id={id} rows={3} value={f.address} autoComplete="street-address" placeholder="Street, area, city and PIN code" onChange={(e) => setF({ ...f, address: e.target.value })} />}</Field>
        <Field label="Phone" optional hint="Members call this number. It shows in their app.">{(id) => <input className="rl-field__input" id={id} type="tel" inputMode="tel" autoComplete="off" enterKeyHint="done" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />}</Field>
        <fieldset className="rl-fieldset"><legend>Opening hours</legend>
          <p className="rl-field__hint" style={{ margin: "0 0 var(--space-2)" }}>Split the day into named sessions, with a break between them if the gym closes. Attendance groups check-ins by these sessions; a check-in during a break counts toward the next one.</p>
          <ul className="rl-sessions">
            {rows.map((r, i) => {
              const problem = checked ? rowProblem(r) : undefined;
              return (
                <li className={`rl-session${problem ? " is-invalid" : ""}`} key={i}>
                  <div className="rl-session__top">
                    <label className="rl-session__name">
                      <span className="rl-visually-hidden">Session name</span>
                      <input className="rl-field__input" value={r.name} autoComplete="off" autoCapitalize="words" placeholder="Name, for example Morning" aria-invalid={(problem && !r.name.trim()) || undefined} onChange={(e) => setRow(i, "name", e.target.value)} />
                    </label>
                    <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Remove ${r.name || "this session"}`} onClick={() => setRows(rows.filter((_, j) => j !== i))}><Icon as={Trash2} size="sm" /></button>
                  </div>
                  <div className="rl-session__times">
                    <ClockPick label="Opens" value={r.starts} invalid={!!problem && (!r.starts || (!!r.ends && r.ends <= r.starts))} onChange={(t) => setRow(i, "starts", t)} />
                    <ClockPick label="Closes" value={r.ends} invalid={!!problem && (!r.ends || (!!r.starts && r.ends <= r.starts))} onChange={(t) => setRow(i, "ends", t)} />
                  </div>
                  <ErrorText>{problem}</ErrorText>
                </li>
              );
            })}
          </ul>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" style={{ marginTop: "var(--space-2)" }} onClick={() => { setRows([...rows, { name: "", starts: rows.at(-1)?.ends ?? "06:00", ends: "" }]); setRowsErr(undefined); }}><Icon as={Plus} />Add Session</button>
          <ErrorText>{rowsErr ?? sessionsMsg}</ErrorText>
        </fieldset>
        <fieldset className="rl-fieldset"><legend>Days open</legend>
          <Chips name="days" label="Days open" scroll={false} value={f.days_open} onChange={(v) => setF({ ...f, days_open: v })} options={[{ value: "every_day", label: "Every day" }, { value: "mon_sat", label: "Monday to Saturday" }]} />
        </fieldset>
        {branch && (
          <Section label="Wall QR">
            <Link className="rl-button rl-button--secondary rl-button--block" href={`/branches/${branch.id}/qr`}><Icon as={QrCode} />Print Check-in QR</Link>
          </Section>
        )}
        {branch && (
          <Section label="Status">
            <button className={`rl-button rl-button--block ${branch.is_active ? "rl-button--danger-quiet" : "rl-button--secondary"}`} type="button" onClick={() => save({ is_active: !branch.is_active })}>{branch.is_active ? "Mark Branch Closed" : "Reopen Branch"}</button>
          </Section>
        )}
        <ErrorText>{a.error && !sessionsMsg ? a.error.message : undefined}</ErrorText>
      </form>
      <ActionBar label={branch ? "Save Changes" : "Add Branch"} onClick={() => save()} busy={a.busy} />
    </>
  );
}
