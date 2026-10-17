"use client";
import {
  BellRing, CalendarCheck, CircleCheck, Dumbbell, KeyRound, Mail, MapPin, MessageCircle, MoreHorizontal, Pause, Pencil, Phone, Play, StickyNote, Target, Trash2, UserRound,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { useCheckinsList } from "@/api/gen/checkins/checkins";
import { useMembersRetrieve } from "@/api/gen/members/members";
import { useMessagesList } from "@/api/gen/messages/messages";
import type { CurrentPlan, Member, Note, Payment } from "@/api/gen/model";
import { usePaymentsListInfinite } from "@/api/gen/payments/payments";
import { useStaffList } from "@/api/gen/staff/staff";
import { useSubscriptionsRetrieve } from "@/api/gen/subscriptions/subscriptions";
import { DetailBar } from "@/components/shell";
import { Details, ErrorText, Field, Icon, LoadMore, Photo, Section, Setting, Sheet, SkeletonRows, Status } from "@/components/ui";
import { CheckInResult, useCheckIn } from "@/features/checkin";
import { day, daysLeft, isoDate, phone, rupees } from "@/lib/format";
import { paged, pages, useAction, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TrainerMember } from "@/lib/types";

export default function MemberProfile() {
  const { id } = useParams<{ id: string }>();
  const mid = Number(id);
  const { role } = useSession();
  const desk = role.role === "admin" || role.role === "receptionist";
  const q = useMembersRetrieve(mid);
  const m = q.data?.data as (Member & Partial<TrainerMember>) | undefined;
  // Payments come a few at a time, newest first: a long-time member's history never loads all at once.
  const paysQ = usePaymentsListInfinite({ member: mid, limit: 5 }, { query: { ...paged, enabled: desk } });
  const pays = pages(paysQ).rows;
  // The current plan's price, offer and what's been paid toward it, for the membership card (desk only: amounts).
  const planId = (q.data?.data as Member | undefined)?.plan?.id;
  const subQ = useSubscriptionsRetrieve(planId ?? 0, { query: { enabled: desk && !!planId } });
  const visits = useCheckinsList({ member: mid, limit: 10 });
  const notes = useGet<Note[]>(`/api/members/${mid}/notes/`, undefined, role.role !== "member");
  const { checkIn, outcome, busy, close } = useCheckIn();
  const [sheet, setSheet] = useState<null | "more" | "note" | "freeze" | "login" | "edit" | "archive" | { void: Payment }>(null);
  const today = isoDate(new Date());
  const inToday = visits.data?.data.results.find((c) => c.local_date === today);

  if (q.isError) return <div className="rl-app rl-root"><DetailBar title="Member" /><main className="rl-app__main"><p className="rl-row__meta">This member couldn&apos;t be found.</p></main></div>;
  if (!m) return <div className="rl-app rl-root"><DetailBar title="Member" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;

  const plan = m.plan as (Partial<CurrentPlan> & { name: string; starts: string; ends: string }) | null | undefined;
  const ends = plan?.ends ?? m.plan_ends ?? null;
  const current = desk && plan?.id ? (plan as CurrentPlan) : null;  // the plan the desk can freeze or unfreeze
  const balance = m.balance_paise ?? 0;
  const sub = subQ.data?.data;
  const digits = m.phone.replace(/\D/g, "").slice(-10);

  return (
    <div className="rl-app rl-root">
      <DetailBar title="Member" action={desk ? <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="More actions" aria-haspopup="dialog" onClick={() => setSheet("more")}><Icon as={MoreHorizontal} /></button> : undefined} />
      <main className="rl-app__main">
        <div className="rl-identity">
          <Photo name={m.name} size="xl" />
          <div className="rl-identity__text">
            <h2 className="rl-identity__name">{m.name}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{m.code}</span><Status status={m.status} /></p>
          </div>
        </div>

        <Section label="Actions">
          <div className="rl-actions">
            {desk && (inToday ? (
              <p className="rl-button" role="status" aria-label={`Checked in at ${inToday.time}`} title={`Checked in at ${inToday.time}`}
                style={{ background: "var(--volt-soft)", color: "var(--ink)", boxShadow: "none", cursor: "default" }}>
                <Icon as={CircleCheck} />In at {inToday.time}
              </p>
            ) : (
              <button className="rl-button rl-button--accent" type="button" disabled={busy === m.id} onClick={() => checkIn(m as Member)}>{busy === m.id ? "Checking in…" : "Check In"}</button>
            ))}
            {desk && (balance > 0
              ? <Link className="rl-button rl-button--secondary" href={`/payments/new?member=${m.id}`}>Collect {rupees(balance)}</Link>
              : <Link className="rl-button rl-button--secondary" href={`/subscriptions/new?member=${m.id}`}>{m.status === "expired" || m.status === "expiring" || m.status === "none" ? "Renew Membership" : "New Subscription"}</Link>)}
            <div className="rl-actions__contact">
              <a className="rl-button rl-button--secondary rl-button--sm" href={`tel:+91${digits}`}><Icon as={Phone} size="sm" />Call</a>
              <a className="rl-button rl-button--secondary rl-button--sm" href={`https://wa.me/91${digits}`} target="_blank" rel="noreferrer"><Icon as={MessageCircle} size="sm" />WhatsApp</a>
            </div>
          </div>
        </Section>

        <div className="rl-app__cols">
          <div className="rl-app__col">
            <Section title="Membership">
              {plan || ends ? (
                <div className={`rl-pass${m.status === "expired" ? " rl-pass--expired" : m.status === "expiring" ? " rl-pass--renew" : ""}`}>
                  <div className="rl-pass__top"><Status status={m.status} /><span className="rl-pass__plan">{plan?.name ?? "Membership"}</span></div>
                  {ends && <p className="rl-figure">{Math.max(0, daysLeft(ends) + 1)} <small>{m.status === "expired" ? "days left" : "days remaining"}</small></p>}
                  <div className="rl-pass__dates"><span>{plan?.starts ? day(plan.starts) : ""}</span><span>{m.status === "expired" ? "Expired" : "Expires"} {ends ? day(ends) : ""}</span></div>
                  {desk && (sub || balance > 0) && (
                    <div className="rl-sub">
                      {sub && <span><strong>Price:</strong> {rupees(sub.price_paise)}{sub.offer_name ? ` with ${sub.offer_name} (was ${rupees(sub.list_price_paise)})` : ""}</span>}
                      {sub && <span><strong>Paid:</strong> {rupees(sub.paid_paise)}{sub.paid_paise < sub.price_paise ? ` of ${rupees(sub.price_paise)}` : " in full"}</span>}
                      {balance > 0 && <span><strong>Payment due:</strong> {rupees(balance)}</span>}
                    </div>
                  )}
                  {!desk && m.payment_due && <div className="rl-sub"><span><strong>Payment due.</strong> The front desk will collect it.</span></div>}
                  {current?.frozen_from && <div className="rl-sub"><span><strong>Frozen</strong> {day(current.frozen_from)} to {current.frozen_until ? day(current.frozen_until) : "further notice"}</span></div>}
                </div>
              ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No plan yet.</p></div>}
            </Section>
            <Section title="Details">
              <Details rows={[
                { icon: Phone, label: "Mobile number", value: phone(m.phone) },
                ...(desk ? [{ icon: Mail, label: "Email", value: m.email }] : []),
                { icon: MapPin, label: "Home branch", value: typeof m.home_branch === "string" ? m.home_branch : role.branches.find((b) => b.id === m.home_branch)?.name },
                ...(desk ? [{ icon: Dumbbell, label: "Trainer", value: m.trainer_name ?? "Not set" }] : []),
                { icon: Target, label: "Goal", value: m.goal || "Not set" },
                ...(desk ? [{ icon: CalendarCheck, label: "Joined", value: m.joined_on ? day(m.joined_on) : "" }, { icon: KeyRound, label: "App login", value: m.has_login ? "Set. Signs in with their mobile number" : "Not set" }] : []),
              ].filter((r) => r.value !== undefined)} />
            </Section>
          </div>
          <div className="rl-app__col">
            {desk && (
              <Section title="Payments">
                {paysQ.isLoading ? <SkeletonRows n={2} /> : pays.length ? (
                  <><ul className="rl-card rl-mlist rl-mlist--compact">
                    {pays.map((p) => (
                      <li key={p.id}><button className="rl-mrow" type="button" disabled={role.role !== "admin" || p.voided} onClick={() => setSheet({ void: p })}>
                        <span className="rl-chipicon" aria-hidden="true"><Icon as={UserRound} size="sm" /></span>
                        <span className="rl-row__title rl-mrow__name" style={p.voided ? { textDecoration: "line-through" } : undefined}>{rupees(p.amount_paise)} by {p.method.toUpperCase()}</span>
                        <span className="rl-row__meta rl-mrow__meta">{day(p.taken_at)} • {p.taken_by_name}{p.voided ? ` • Voided: ${p.void_reason}` : ""}</span>
                      </button></li>
                    ))}
                  </ul><LoadMore q={paysQ} /></>
                ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No payments yet.</p></div>}
              </Section>
            )}
            <Section title="Recent visits">
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
              ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No visits yet.</p></div>}
            </Section>
            {desk && <RemindersCard member={m} />}
            {role.role !== "member" && (
              <Section title="Notes" aside={<button className="rl-link rl-link--plain" type="button" onClick={() => setSheet("note")}><span>Add Note</span></button>}>
                {notes.data?.length ? (
                  <ul className="rl-card rl-notes">
                    {notes.data.map((n) => <li key={n.id} style={{ padding: "var(--space-3) var(--space-4)" }}><p style={{ margin: 0 }}>{n.text}</p><p className="rl-row__meta" style={{ margin: 0 }}>{n.author} • {day(n.created_at)}</p></li>)}
                  </ul>
                ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No notes yet. Notes are seen by staff only.</p></div>}
              </Section>
            )}
          </div>
        </div>
      </main>

      <CheckInResult outcome={outcome} onClose={close} />
      <Sheet open={sheet === "more"} onClose={() => setSheet(null)} title="Member actions">
        <ul className="rl-sheet__list">
          <SheetItem icon={Pencil} label="Edit Details" onClick={() => setSheet("edit")} />
          <SheetItem icon={StickyNote} label="Add Note" onClick={() => setSheet("note")} />
          {current && (current.frozen_from
            ? <SheetItem icon={Play} label="Unfreeze Membership" onClick={() => setSheet("freeze")} />
            : <SheetItem icon={Pause} label="Freeze Membership" onClick={() => setSheet("freeze")} />)}
          <SheetItem icon={KeyRound} label={m.has_login ? "Reset App Password" : "Set Up App Login"} onClick={() => setSheet("login")} />
          {role.role === "admin" && <SheetItem icon={Trash2} label="Archive Member" onClick={() => setSheet("archive")} />}
        </ul>
      </Sheet>
      <NoteSheet open={sheet === "note"} id={mid} onClose={() => setSheet(null)} />
      {current && <FreezeSheet open={sheet === "freeze"} sub={current} onClose={() => setSheet(null)} />}
      <LoginSheet open={sheet === "login"} member={m} onClose={() => setSheet(null)} />
      {desk && <EditSheet open={sheet === "edit"} member={m} onClose={() => setSheet(null)} />}
      <ArchiveSheet open={sheet === "archive"} member={m} onClose={() => setSheet(null)} />
      <VoidSheet payment={typeof sheet === "object" && sheet ? sheet.void : null} onClose={() => setSheet(null)} />
    </div>
  );
}

/** What the gym has messaged this member lately, and whether to go on messaging them. */
function RemindersCard({ member }: { member: Member }) {
  const q = useMessagesList({ member: member.id, limit: 5 });
  const rows = q.data?.data.results ?? [];
  const a = useAction();
  async function setOn(on: boolean) {
    try {
      await a.run(`/api/members/${member.id}/`, { reminders_opted_out: !on }, { method: "PATCH", refresh: [`/api/members/${member.id}/`] });
    } catch { /* shown under the switch */ }
  }
  return (
    <Section title="Reminders">
      {q.isLoading ? <SkeletonRows n={2} /> : (
        <div className="rl-card">
          {rows.length ? (
            <ul className="rl-mlist rl-mlist--compact">
              {rows.map((msg) => (
                <li key={msg.id}><div className="rl-mrow">
                  <span className="rl-chipicon rl-mrow__lead" aria-hidden="true"><Icon as={BellRing} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{msg.kind_label}</span>
                  <span className="rl-row__meta rl-mrow__meta">{msg.status === "failed" ? msg.error || "It didn't go" : msg.text}</span>
                  <span className={`rl-mrow__note${msg.status === "failed" ? " rl-mrow__note--alert" : ""}`}>
                    {msg.status === "failed" ? "Didn't send" : day(msg.for_date)}
                  </span>
                </div></li>
              ))}
            </ul>
          ) : (
            <p className="rl-row__meta" style={{ margin: 0, padding: "var(--space-3) var(--space-4)" }}>
              {member.reminders_opted_out ? "Reminders are off for this member." : "Nothing sent yet. Reminders go out at 6 am when a plan is ending or money is owed."}
            </p>
          )}
          <Setting
            name="member-reminders"
            title="Send this member reminders"
            note={member.reminders_opted_out ? "Off: they are never messaged" : "Renewals and payments due, on WhatsApp"}
            checked={!member.reminders_opted_out}
            disabled={a.busy}
            onChange={setOn}
          />
        </div>
      )}
      <ErrorText>{a.error?.message}</ErrorText>
    </Section>
  );
}

function SheetItem({ icon, label, onClick }: { icon: typeof Pencil; label: string; onClick: () => void }) {
  return <li><button className="rl-sheet__item" type="button" onClick={onClick}><span className="rl-chipicon"><Icon as={icon} size="sm" /></span><span className="rl-sheet__text">{label}</span></button></li>;
}

function NoteSheet({ open, id, onClose }: { open: boolean; id: number; onClose: () => void }) {
  const [text, setText] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function save() {
    if (!text.trim()) return setErr("Write the note first");
    try { await a.run(`/api/members/${id}/notes/`, { text: text.trim() }, { refresh: [`/api/members/${id}/notes/`] }); setText(""); onClose(); } catch { /* shown below */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Add Note">
      <Field label="Note" error={err} area hint="Only staff see notes.">
        {(fid) => <textarea className="rl-field__input" id={fid} rows={3} value={text} onChange={(e) => { setText(e.target.value); setErr(undefined); }} placeholder="Prefers evening sessions" />}
      </Field>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Note"}</button></div>
    </Sheet>
  );
}

function FreezeSheet({ open, sub, onClose }: { open: boolean; sub: CurrentPlan; onClose: () => void }) {
  const [until, setUntil] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  const frozen = !!sub.frozen_from;
  async function go() {
    if (!frozen && !until) return setErr("Choose the last day of the freeze");
    try { await a.run(`/api/subscriptions/${sub.id}/${frozen ? "unfreeze" : "freeze"}/`, frozen ? {} : { until }); onClose(); } catch { /* shown */ }
  }
  const days = until ? Math.max(0, daysLeft(until) + 1) : 0;
  return (
    <Sheet open={open} onClose={onClose} title={frozen ? "Unfreeze Membership" : "Freeze Membership"}>
      {frozen ? (
        <p className="rl-row__meta">The membership starts running again today. Days not used come off the end date.</p>
      ) : (
        <Field label="Frozen until" error={err} hint={days ? `The end date moves out by ${days} days, to after ${day(sub.ends)}.` : "Freezing pauses the plan from today. The end date moves out by the days frozen."}>
          {(fid) => <input className="rl-field__input" id={fid} type="date" min={isoDate(new Date())} value={until} onChange={(e) => { setUntil(e.target.value); setErr(undefined); }} />}
        </Field>
      )}
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Saving…" : frozen ? "Unfreeze" : "Freeze"}</button></div>
    </Sheet>
  );
}

function LoginSheet({ open, member, onClose }: { open: boolean; member: Member; onClose: () => void }) {
  const [pw, setPw] = useState("");
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function go() {
    if (pw.length < 6) return setErr("Use at least 6 characters");
    try { await a.run(`/api/members/${member.id}/set-login/`, { password: pw }); setDone(true); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={() => { setDone(false); setPw(""); onClose(); }} title={done ? undefined : "App login"}>
      {done ? (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">Login is ready</h2><p className="rl-confirm__text">{member.name} signs in with {phone(member.phone)} and the password you set.</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={() => { setDone(false); setPw(""); onClose(); }}>Done</button></div>
        </>
      ) : (
        <>
          <p className="rl-row__meta">{member.name} signs in to the app with their mobile number, {phone(member.phone)}.</p>
          <Field label="Password" error={err} hint="Tell them the password. They can't change it themselves yet.">
            {(fid) => <input className="rl-field__input" id={fid} type="text" autoComplete="new-password" value={pw} onChange={(e) => { setPw(e.target.value); setErr(undefined); }} />}
          </Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Saving…" : "Set Password"}</button></div>
        </>
      )}
    </Sheet>
  );
}

function EditSheet({ open, member, onClose }: { open: boolean; member: Member; onClose: () => void }) {
  const trainers = useStaffList({ role: "trainer", is_active: true, limit: 100 });
  const [f, setF] = useState({ name: member.name, phone: member.phone.replace(/^\+91/, ""), email: member.email ?? "", goal: member.goal ?? "", trainer: member.trainer ?? null as number | null });
  const a = useAction();
  async function save() {
    try { await a.run(`/api/members/${member.id}/`, { ...f, trainer: f.trainer || null }, { method: "PATCH" }); onClose(); } catch { /* shown */ }
  }
  const fe = (k: string) => { const v = a.error?.fields?.[k]; return Array.isArray(v) ? String(v[0]) : undefined; };
  return (
    <Sheet open={open} onClose={onClose} title="Edit Details">
      <Field label="Full name" error={fe("name")}>{(id) => <input className="rl-field__input" id={id} value={f.name} autoComplete="off" onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
      <Field label="Mobile number" prefix="+91" error={fe("phone")}>{(id) => <input className="rl-field__input" id={id} type="tel" inputMode="numeric" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />}</Field>
      <Field label="Email" optional error={fe("email")}>{(id) => <input className="rl-field__input" id={id} type="email" inputMode="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />}</Field>
      <Field label="Trainer" optional>{(id) => (
        <select className="rl-field__input" id={id} value={f.trainer ?? ""} onChange={(e) => setF({ ...f, trainer: e.target.value ? Number(e.target.value) : null })}>
          <option value="">No trainer</option>
          {(trainers.data?.data.results ?? []).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      )}</Field>
      <Field label="Goal" optional>{(id) => <input className="rl-field__input" id={id} value={f.goal} placeholder="Weight loss" onChange={(e) => setF({ ...f, goal: e.target.value })} />}</Field>
      <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Changes"}</button></div>
    </Sheet>
  );
}

function ArchiveSheet({ open, member, onClose }: { open: boolean; member: Member; onClose: () => void }) {
  const a = useAction();
  const router = useRouter();
  async function go() {
    try { await a.run(`/api/members/${member.id}/`, undefined, { method: "DELETE" }); router.push("/members"); } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Archive this member?">
      <p className="rl-row__meta">{member.name} leaves the members list and can&apos;t check in or sign in. Their payments and visits stay on record.</p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Archiving…" : "Archive Member"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep Member</button>
      </div>
    </Sheet>
  );
}

function VoidSheet({ payment, onClose }: { payment: Payment | null; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  async function go() {
    if (!reason.trim()) return setErr("Say why, for the record");
    try { await a.run(`/api/payments/${payment!.id}/void/`, { reason: reason.trim() }); setReason(""); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!payment} onClose={onClose} title="Void this payment?">
      {payment && <p className="rl-row__meta">{rupees(payment.amount_paise)} by {payment.method.toUpperCase()} on {day(payment.taken_at)}. It stays on record, marked void, and the amount is owed again.</p>}
      <Field label="Reason" error={err}>{(id) => <input className="rl-field__input" id={id} value={reason} placeholder="Entered twice" onChange={(e) => { setReason(e.target.value); setErr(undefined); }} />}</Field>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Voiding…" : "Void Payment"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep Payment</button>
      </div>
    </Sheet>
  );
}
