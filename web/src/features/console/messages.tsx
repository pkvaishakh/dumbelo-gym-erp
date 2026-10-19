"use client";
/* When messages go out, in the Console: Dumbelo's times for every gym (Automation) and one gym's messages, with
   its own times and Use Dumbelo's Times. Gyms only pause and resume their own messages; the times are set here. */
import type { LucideIcon } from "lucide-react";
import { AlertCircle, BadgeIndianRupee, CalendarClock, CalendarX, ClipboardList, FileText, Receipt, ReceiptText } from "lucide-react";
import { useState } from "react";

import type { AutomationSchedule, Rule } from "@/api/gen/model";
import { usePlatformGymsMessagesList } from "@/api/gen/platform/platform";
import { Empty, ErrorText, Field, Icon, MenuRow, Section, Setting, Sheet, SkeletonRows } from "@/components/ui";
import { fieldError, useAction } from "@/lib/hooks";
import { DAY_CHOICES, daysLabel, hourLabel, HOURS, MAX_WARNINGS, MESSAGE_TO, whenLabel } from "@/lib/messages";

const ICON: Record<string, LucideIcon> = {
  plan_ending: CalendarClock, plan_ends_today: CalendarX, payment_due: BadgeIndianRupee, payment_received: Receipt,
  task_assigned: ClipboardList, dumbelo_invoice_due: FileText, dumbelo_payment_received: ReceiptText,
};

/** An hour of the day on the gym's own clock. */
export function HourField({ label, value, onChange, error, hint }: {
  label: string; value: number; onChange: (h: number) => void; error?: string; hint?: React.ReactNode;
}) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(id, d) => (
        <select className="rl-field__input" id={id} aria-describedby={d} value={value} onChange={(e) => onChange(Number(e.target.value))}>
          {HOURS.map((h) => <option key={h} value={h}>{hourLabel(h)}</option>)}
        </select>
      )}
    </Field>
  );
}

/** How many days before a plan ends members are warned: up to 3, picked as chips. */
export function DaysField({ value, onChange, error }: { value: number[]; onChange: (days: number[]) => void; error?: string }) {
  const choices = [...new Set([...DAY_CHOICES, ...value])].sort((a, b) => a - b); // a day set before stays on offer
  const full = value.length >= MAX_WARNINGS;
  return (
    <fieldset className="rl-fieldset">
      <legend>Days before a plan ends</legend>
      <div className="rl-chips">
        {choices.map((n) => {
          const on = value.includes(n);
          return (
            <label className="rl-chipopt" key={n}>
              <input type="checkbox" checked={on} disabled={!on && full} onChange={() => onChange(on ? value.filter((v) => v !== n) : [...value, n])} />
              <span>{n === 1 ? "1 day" : `${n} days`}</span>
            </label>
          );
        })}
      </div>
      {error ? <ErrorText>{error}</ErrorText> : <p className="rl-field__hint">Pick up to {MAX_WARNINGS}. {value.length ? `Now: ${daysLabel(value)}.` : ""}</p>}
    </fieldset>
  );
}

/** Edit Times: Dumbelo's reminder hour, days ahead and invoice hour, for every gym without its own. */
export function AutomationSheet({ schedule, open, onClose }: { schedule: AutomationSchedule; open: boolean; onClose: () => void }) {
  const fresh = () => ({ reminder_hour: schedule.reminder_hour, days_ahead: schedule.days_ahead, invoice_hour: schedule.invoice_hour });
  const [f, setF] = useState(fresh);
  const [was, setWas] = useState(false);
  const [err, setErr] = useState<string>();
  if (open !== was) { // start from what's saved each time the sheet opens
    setWas(open);
    if (open) setF(fresh());
  }
  const a = useAction();
  const close = () => { setErr(undefined); a.clearError(); onClose(); };
  async function save() {
    if (!f.days_ahead.length) return setErr("Pick at least one day");
    setErr(undefined);
    try {
      await a.run("/api/platform/automation/", f, { method: "PATCH", refresh: ["/api/platform/automation/", "/api/platform/gyms/"] });
      close();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title="Edit Times">
      <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
        <HourField label="Reminders go out at" value={f.reminder_hour} onChange={(reminder_hour) => setF({ ...f, reminder_hour })}
          error={fieldError(a.error, "reminder_hour")} hint="On each gym's own clock. Dumbelo's invoice reminders to owners go at this hour too." />
        <DaysField value={f.days_ahead} onChange={(days_ahead) => setF({ ...f, days_ahead })} error={err ?? fieldError(a.error, "days_ahead")} />
        <HourField label="Invoices are written at" value={f.invoice_hour} onChange={(invoice_hour) => setF({ ...f, invoice_hour })}
          error={fieldError(a.error, "invoice_hour")} hint="On a gym's billing day, on its own clock." />
        <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="submit" disabled={a.busy}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
      </form>
    </Sheet>
  );
}

/** One of a gym's messages: Pause or Resume for Dumbelo's own, and this gym's times for the ones sent at an hour. */
function MessageSheet({ gymId, rule, onClose }: { gymId: number; rule: Rule | null; onClose: () => void }) {
  const [f, setF] = useState({ hour: 0, days: [] as number[] });
  const [kind, setKind] = useState<string | null>(null);
  if ((rule?.kind ?? null) !== kind) { // start from what's saved each time the sheet opens
    setKind(rule?.kind ?? null);
    if (rule) setF({ hour: rule.hour ?? 0, days: rule.days_ahead ?? [] });
  }
  const a = useAction();
  const url = `/api/platform/gyms/${gymId}/messages/${rule?.kind}/`;
  const refresh = [`/api/platform/gyms/${gymId}/messages/`];
  const close = () => { a.clearError(); onClose(); };
  async function send(body: object, done = true) {
    try {
      await a.run(url, body, { method: "PATCH", refresh });
      if (done) close();
    } catch { /* shown */ }
  }
  const scheduled = rule?.hour != null;
  const days = rule?.kind === "plan_ending";
  return (
    <Sheet open={!!rule} onClose={close} title={rule?.label ?? ""}>
      {rule && (
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); send(days ? { hour: f.hour, days_ahead: f.days } : { hour: f.hour }); }}>
          <p className="rl-row__meta" style={{ margin: 0 }}>{MESSAGE_TO[rule.kind]} • {whenLabel(rule)}{rule.gyms_own_time ? " • This gym's own time" : ""}</p>
          {rule.switched_by === "dumbelo" && (
            <div className="rl-card">
              <Setting name={`send-${rule.kind}`} title="Send it" note={rule.is_on ? "On for this gym" : "Paused for this gym"} checked={rule.is_on}
                disabled={a.busy} onChange={(on) => send({ is_on: on }, false)} />
            </div>
          )}
          {scheduled && (
            <>
              <HourField label="Goes out at" value={f.hour} onChange={(hour) => setF({ ...f, hour })} error={fieldError(a.error, "hour")}
                hint="On the gym's own clock. Saving makes it this gym's own time, in place of Dumbelo's." />
              {days && <DaysField value={f.days} onChange={(d) => setF({ ...f, days: d })} error={fieldError(a.error, "days_ahead")} />}
            </>
          )}
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          {scheduled && (
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="submit" disabled={a.busy || (days && !f.days.length)}>{a.busy ? "Saving…" : "Save Times"}</button>
              {rule.gyms_own_time && (
                <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy}
                  onClick={() => send({ hour: null, days_ahead: null })}>Use Dumbelo&apos;s Times</button>
              )}
            </div>
          )}
        </form>
      )}
    </Sheet>
  );
}

/** How a message stands in a row: its hour (marked when it's the gym's own), and Paused when it is. */
function standing(r: Rule) {
  const time = r.hour != null ? `${hourLabel(r.hour)}${r.gyms_own_time ? ", own time" : ""}` : null;
  if (!r.is_on) return time ? `Paused • ${time}` : "Paused";
  return time ?? "On";
}

/** A gym's messages on its Console screen: when each goes out and whether it's on. The gym's own switches are its
 *  admins' to flip, so those rows only say how they stand. */
export function GymMessages({ gymId }: { gymId: number }) {
  const q = usePlatformGymsMessagesList(gymId);
  const [open, setOpen] = useState<string | null>(null);
  const rules = q.data?.data;
  const rule = rules?.find((r) => r.kind === open) ?? null;
  return (
    <Section title="Messages">
      {q.isLoading ? <SkeletonRows n={4} /> : q.isError || !rules ? (
        <Empty icon={AlertCircle} title="Can't load its messages" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      ) : (
        <>
          <ul className="rl-card rl-remind">
            {rules.map((r) => {
              const icon = ICON[r.kind] ?? FileText;
              if (r.hour != null || r.switched_by === "dumbelo") {
                return <MenuRow key={r.kind} icon={icon} title={r.label} value={standing(r)} onClick={() => setOpen(r.kind)} />;
              }
              return ( // the gym's own switch, sent as it happens: nothing for Dumbelo to set
                <li key={r.kind}><div className="rl-remind__row">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={icon} size="sm" /></span>
                  <span className="rl-remind__text"><span className="rl-row__title">{r.label}</span></span>
                  <span className="rl-menu__value">{standing(r)}</span>
                </div></li>
              );
            })}
          </ul>
          <p className="rl-row__meta">The gym&apos;s admins pause and resume its own messages. Times without &ldquo;own time&rdquo; are Dumbelo&apos;s, from Automation.</p>
        </>
      )}
      <MessageSheet gymId={gymId} rule={rule} onClose={() => setOpen(null)} />
    </Section>
  );
}
