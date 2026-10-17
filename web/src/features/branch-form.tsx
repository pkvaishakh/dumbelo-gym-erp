"use client";
import { Plus, QrCode, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { Branch } from "@/api/gen/model";
import { Choices, ErrorText, Field, Icon, Section } from "@/components/ui";
import { span } from "@/lib/format";
import { useAction } from "@/lib/hooks";

import { ActionBar } from "./sell";

type Row = { name: string; starts: string; ends: string };
const DEFAULT: Row[] = [{ name: "Morning", starts: "05:00", ends: "10:00" }, { name: "Evening", starts: "17:00", ends: "22:00" }];

/** Add Branch / Edit Branch: details and opening hours as named sessions (Morning 5–10 AM, Evening 5–10 PM…). */
export function BranchForm({ branch, onSaved }: { branch?: Branch; onSaved: (b: Branch) => void }) {
  const [f, setF] = useState({ name: branch?.name ?? "", address: branch?.address ?? "", phone: branch?.phone ?? "", days_open: branch?.days_open ?? "every_day" });
  const [rows, setRows] = useState<Row[]>(branch ? branch.sessions.map((s) => ({ name: s.name, starts: s.starts.slice(0, 5), ends: s.ends.slice(0, 5) })) : DEFAULT);
  const [err, setErr] = useState<string>();
  const a = useAction();
  const setRow = (i: number, k: keyof Row, v: string) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)));

  async function save(extra?: object) {
    if (!f.name.trim()) return setErr("Enter the branch name");
    if (!rows.length) return setErr("Add at least one session");
    for (const r of rows) if (!r.name.trim() || !r.starts || !r.ends) return setErr("Name every session and give it a start and end");
    setErr(undefined);
    try {
      const b = await a.run<Branch>(branch ? `/api/branches/${branch.id}/` : "/api/branches/", { ...f, name: f.name.trim(), sessions: rows, ...extra }, { method: branch ? "PATCH" : "POST", refresh: ["/api/branches/", "/api/me/"] });
      onSaved(b!);
    } catch { /* shown */ }
  }
  const apiMsg = a.error ? (Array.isArray(a.error.fields?.sessions) ? String((a.error.fields!.sessions as string[])[0]) : a.error.message) : undefined;
  return (
    <>
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <Field label="Branch name">{(id) => <input className="rl-field__input" id={id} value={f.name} placeholder="Indiranagar" onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
        <Field label="Address" optional area>{(id) => <textarea className="rl-field__input" id={id} rows={2} value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} />}</Field>
        <Field label="Phone" optional>{(id) => <input className="rl-field__input" id={id} type="tel" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />}</Field>
        <fieldset className="rl-fieldset"><legend>Open</legend>
          <Choices name="days" two value={f.days_open} onChange={(v) => setF({ ...f, days_open: v })} options={[{ value: "every_day", title: "Every day" }, { value: "mon_sat", title: "Monday to Saturday" }]} />
        </fieldset>
        <Section title="Opening hours" aside={<p className="rl-section__aside">Check-ins are grouped by these</p>}>
          <ul className="rl-card" style={{ listStyle: "none", margin: 0, padding: "var(--space-2) var(--space-4)" }}>
            {rows.map((r, i) => (
              <li key={i} style={{ padding: "var(--space-2) 0", borderBottom: i < rows.length - 1 ? "1px solid var(--line)" : undefined }}>
                <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-end" }}>
                  <div style={{ flex: 1 }}><Field label="Name">{(id) => <input className="rl-field__input" id={id} value={r.name} onChange={(e) => setRow(i, "name", e.target.value)} />}</Field></div>
                  <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={`Remove ${r.name || "session"}`} onClick={() => setRows(rows.filter((_, j) => j !== i))} style={{ marginBottom: 6 }}><Icon as={Trash2} size="sm" /></button>
                </div>
                <div className="rl-pair">
                  <Field label="Opens">{(id) => <input className="rl-field__input" id={id} type="time" value={r.starts} onChange={(e) => setRow(i, "starts", e.target.value)} />}</Field>
                  <Field label="Closes">{(id) => <input className="rl-field__input" id={id} type="time" value={r.ends} onChange={(e) => setRow(i, "ends", e.target.value)} />}</Field>
                </div>
                {r.starts && r.ends && <p className="rl-field__hint" style={{ margin: 0 }}>{span(r.starts, r.ends)}</p>}
              </li>
            ))}
          </ul>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" style={{ marginTop: "var(--space-3)" }} onClick={() => setRows([...rows, { name: "", starts: rows.at(-1)?.ends ?? "06:00", ends: "" }])}><Icon as={Plus} />Add Session</button>
          <p className="rl-field__hint">A check-in during a break counts toward the next session.</p>
        </Section>
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
        <ErrorText>{err ?? apiMsg}</ErrorText>
      </form>
      <ActionBar label={branch ? "Save Changes" : "Add Branch"} onClick={() => save()} busy={a.busy} />
    </>
  );
}
