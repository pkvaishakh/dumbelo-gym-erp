"use client";
import { AtSign, Banknote, CalendarCheck, CalendarOff, Clock, Dumbbell, Fingerprint, Mail, MapPin, Minus, Phone, Pencil, Plus, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useCheckinsList } from "@/api/gen/checkins/checkins";
import { usePayslipsListInfinite } from "@/api/gen/payslips/payslips";
import { useSalaryRulesList } from "@/api/gen/salary-rules/salary-rules";
import { useStaffRetrieve } from "@/api/gen/staff/staff";
import { DetailBar } from "@/components/shell";
import type { Staff } from "@/api/gen/model";
import { Details, ErrorText, Field, Icon, LoadMore, Photo, Section, Sheet, SkeletonRows, Status } from "@/components/ui";
import { PayslipStatus } from "@/features/money-out";
import { rateText } from "@/features/payroll";
import { day, isoDate, monthLabel, PAY_TYPE, phone, rupees } from "@/lib/format";
import { fieldError, paged, pages, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

export default function StaffProfile() {
  const { id } = useParams<{ id: string }>();
  const { role } = useSession();
  const q = useStaffRetrieve(Number(id));
  const s = q.data?.data;
  const visits = useCheckinsList({ staff: Number(id), limit: 14 });
  const [deact, setDeact] = useState(false);
  const [reset, setReset] = useState(false);
  const a = useAction();
  if (!s) return <div className="rl-app rl-root"><DetailBar title="Staff" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  const label = s.role === "trainer" ? "Trainer" : s.role === "receptionist" ? "Receptionist" : "Admin";
  const today = isoDate(new Date());
  async function toggle() {
    try { await a.run(`/api/staff/${s!.id}/`, { is_active: !s!.is_active }, { method: "PATCH", refresh: ["/api/staff/"] }); setDeact(false); } catch { /* shown */ }
  }
  return (
    <div className="rl-app rl-root">
      <DetailBar title={label} action={s.role !== "admin" ? <Link className="rl-iconbtn rl-iconbtn--plain" href={`/staff/${s.id}/edit`} aria-label="Edit"><Icon as={Pencil} /></Link> : undefined} />
      <main className="rl-app__main">
        <div className="rl-identity">
          <Photo name={s.name} size="xl" />
          <div className="rl-identity__text"><h2 className="rl-identity__name">{s.name}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{label}</span>{!s.is_active && <Status status="off" />}</p></div>
        </div>
        <Section title="Details">
          <Details rows={[
            { icon: AtSign, label: "Username", value: `@${s.username}` },
            { icon: Mail, label: "Email", value: s.email || "Not set" },
            { icon: Phone, label: "Mobile number", value: phone(s.phone) },
            { icon: MapPin, label: "Branches", value: s.branches.map((b) => role.branches.find((x) => x.id === b)?.name).filter(Boolean).join(", ") },
            { icon: Clock, label: "Shift", value: s.shift || "Not set" },
            ...(s.role === "trainer" ? [{ icon: Dumbbell, label: "Specialities", value: s.specialities || "Not set" }] : []),
            { icon: CalendarOff, label: "Day off", value: s.day_off || "Not set" },
            { icon: Fingerprint, label: "Turnstile number", value: s.device_user_id || "Not set" },
          ]} />
        </Section>
        {role.role === "admin" && <SalarySection staffId={s.id} />}
        <Section title="Recent check-ins">
          {visits.data?.data.results.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {visits.data.data.results.map((c) => (
                <li key={c.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={CalendarCheck} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{c.local_date === today ? "Today" : day(c.local_date)}</span>
                  <span className="rl-row__meta rl-mrow__meta">{c.branch_name}{c.session ? ` • ${c.session}` : ""}</span>
                  <span className="rl-mrow__time">{c.time}</span>
                </div></li>
              ))}
            </ul>
          ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No check-ins yet.</p></div>}
        </Section>
        {!s.is_owner && s.role !== "admin" && (
          <Section label="Access">
            {role.role === "admin" && s.is_active && (
              <button className="rl-button rl-button--block rl-button--secondary" type="button" style={{ marginBottom: "var(--space-3)" }} onClick={() => setReset(true)}>Reset Password</button>
            )}
            <button className={`rl-button rl-button--block ${s.is_active ? "rl-button--danger-quiet" : "rl-button--secondary"}`} type="button" onClick={() => (s.is_active ? setDeact(true) : toggle())}>
              {s.is_active ? "Deactivate" : "Reactivate"}
            </button>
          </Section>
        )}
      </main>
      <Sheet open={deact} onClose={() => setDeact(false)} title={`Deactivate ${s.name}?`}>
        <p className="rl-row__meta">They can&apos;t sign in or check in until you reactivate them. Their history stays.</p>
        <ErrorText>{a.error?.message}</ErrorText>
        <div className="rl-sheet__actions">
          <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={toggle}>Deactivate</button>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setDeact(false)}>Keep Active</button>
        </div>
      </Sheet>
      {role.role === "admin" && <ResetSheet open={reset} staff={s} onClose={() => setReset(false)} />}
    </div>
  );
}

function ResetSheet({ open, staff, onClose }: { open: boolean; staff: Staff; onClose: () => void }) {
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string>();
  const [done, setDone] = useState(false);
  const a = useAction();
  const close = () => { setPw(""); setErr(undefined); setDone(false); a.clearError(); onClose(); };
  async function go() {
    if (pw.length < 8) return setErr("Use at least 8 characters");
    try { await a.run(`/api/staff/${staff.id}/set-password/`, { password: pw }, { refresh: [] }); setDone(true); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={close} title={done ? undefined : "Reset Password"}>
      {done ? (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">Password reset</h2><p className="rl-confirm__text">{staff.name} signs in as @{staff.username} with the password you set. They&apos;ve been signed out everywhere else.</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <>
          <p className="rl-row__meta">For when {staff.name} has forgotten theirs. They sign in as @{staff.username}.</p>
          <Field label="New password" error={err ?? fieldError(a.error, "password")} hint="At least 8 characters. Tell them the password.">
            {(fid) => <input className="rl-field__input" id={fid} type="text" autoComplete="new-password" value={pw} onChange={(e) => { setPw(e.target.value); setErr(undefined); }} />}
          </Field>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Saving…" : "Set Password"}</button></div>
        </>
      )}
    </Sheet>
  );
}

/** How they're paid and what they've been paid: admins only (the API refuses everyone else). */
function SalarySection({ staffId }: { staffId: number }) {
  const rules = useSalaryRulesList({ staff: staffId });
  const rule = rules.data?.data[0];
  const history = usePayslipsListInfinite({ staff: staffId, limit: 6 }, { query: paged });
  const { rows } = pages(history);
  const items = rule?.items ?? [];
  return (
    <>
      <Section title="Salary" aside={rule ? <Link className="rl-link" href={`/staff/${staffId}/salary/edit`}><span>Change</span></Link> : undefined}>
        {rules.isLoading ? <SkeletonRows n={2} /> : rule ? (
          <Details rows={[
            { icon: Wallet, label: PAY_TYPE[rule.pay_type] ?? "Paid", value: rateText(rule) },
            ...items.filter((i) => i.kind === "allowance").map((i) => ({ icon: Plus, label: `${i.label}, every month`, value: `+${rupees(i.amount_paise)}` })),
            ...items.filter((i) => i.kind === "deduction").map((i) => ({ icon: Minus, label: `${i.label}, every month`, value: `−${rupees(i.amount_paise)}` })),
            { icon: MapPin, label: "Paid from", value: rule.branch_name },
          ]} />
        ) : (
          <div className="rl-card rl-card--pad">
            <p className="rl-row__meta" style={{ marginTop: 0 }}>No salary set, so payroll leaves them out.</p>
            <Link className="rl-button rl-button--secondary rl-button--block" href={`/staff/${staffId}/salary/edit`}>Set Salary</Link>
          </div>
        )}
      </Section>
      {rows.length > 0 && (
        <Section title="Salary history">
          <ul className="rl-card rl-activity">
            {rows.map((p) => (
              <li key={p.id}><Link className="rl-activity__row" href={`/payroll/${p.id}`}>
                <span className="rl-chipicon" aria-hidden="true"><Icon as={Banknote} size="sm" /></span>
                <span className="rl-activity__text"><span className="rl-row__title">{monthLabel(p.month)}</span><span className="rl-row__meta">{rupees(p.paid_paise)} paid of {rupees(p.net_paise)}</span></span>
                <PayslipStatus status={p.status} payment={p.payment_status} />
              </Link></li>
            ))}
          </ul>
          <LoadMore q={history} />
        </Section>
      )}
    </>
  );
}
