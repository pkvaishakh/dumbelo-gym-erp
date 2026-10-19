"use client";
/* Small pieces the Console's screens share. */
import { useMemo } from "react";

import { Field } from "@/components/ui";
import { GYM_STATUS } from "@/lib/format";

export function GymStatus({ status }: { status: string }) {
  const s = GYM_STATUS[status] ?? { label: status, badge: "frozen" };
  return <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>;
}

// Where Dumbelo's gyms are; the browser's own list follows them, for a gym anywhere else.
const NEAR = ["Asia/Kolkata", "Asia/Kathmandu", "Asia/Dhaka", "Asia/Colombo", "Asia/Dubai", "Asia/Singapore"];

/** The gym's time zone: its days start and end there. India's comes first. */
export function TimeZoneField({ value, onChange, error }: { value: string; onChange: (tz: string) => void; error?: string }) {
  const zones = useMemo(() => {
    let all: string[] = [];
    try { all = Intl.supportedValuesOf("timeZone"); } catch { /* an older browser: the nearby ones are enough */ }
    return [...NEAR, ...all.filter((z) => !NEAR.includes(z))];
  }, []);
  return (
    <Field label="Time zone" error={error} hint="The gym's days start and end here: check-ins, payments and reminders follow it.">
      {(id, describedBy) => (
        <select className="rl-field__input" id={id} aria-describedby={describedBy} value={value} onChange={(e) => onChange(e.target.value)}>
          {zones.map((z) => <option key={z} value={z}>{z.replace(/_/g, " ")}</option>)}
        </select>
      )}
    </Field>
  );
}
