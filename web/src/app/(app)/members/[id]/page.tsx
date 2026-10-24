"use client";
import {
  BellRing, CalendarCheck, CalendarClock, CalendarCog, ChevronRight, CircleCheck, Dumbbell, HandHeart, IdCard, IndianRupee, KeyRound, Mail, MapPin, MessageCircle, MoreHorizontal, PartyPopper, Pause, Pencil,
  PenLine, Phone, Play, ReceiptText, Snowflake, StickyNote, Target, Trash2, Undo2, UserRound,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { useCheckinsList } from "@/api/gen/checkins/checkins";
import { useMembersRetrieve } from "@/api/gen/members/members";
import { useMessagesList } from "@/api/gen/messages/messages";
import type { CurrentPlan, LoginSet, Member, Note, Payment, Subscription } from "@/api/gen/model";
import { usePaymentsList } from "@/api/gen/payments/payments";
import { useStaffList } from "@/api/gen/staff/staff";
import { useSubscriptionsList, useSubscriptionsRetrieve } from "@/api/gen/subscriptions/subscriptions";
import { DetailBar } from "@/components/shell";
import { Details, ErrorText, Field, Icon, Photo, Section, Setting, Sheet, SkeletonRows, Status } from "@/components/ui";
import { CheckInResult, useCheckIn } from "@/features/checkin";
import { EditMembershipSheet } from "@/features/plan-correct";
import { METHODS } from "@/features/sell";
import { RefundRows, RefundSheet } from "@/features/refunds";
import { cleanUsername, ExistingLoginField, type LoginKind, LoginKindChips, UsernameField } from "@/features/username";
import { day, daysLeft, gymToday, isoDate, phone, rupees } from "@/lib/format";
import { fieldError, useAction, useGet } from "@/lib/hooks";
import { type Chat, type ChatFacts, type ChatKind, memberChats, membershipChat, nextPlanChat, receiptChat, whatsappLink } from "@/lib/member-chat";
import { useSession } from "@/lib/session";
import type { TrainerMember } from "@/lib/types";

export default function MemberProfile() {
  const { id } = useParams<{ id: string }>();
  const mid = Number(id);
  const { role } = useSession();
  const desk = role.role === "admin" || role.role === "receptionist";
  const q = useMembersRetrieve(mid);
  const m = q.data?.data as (Member & Partial<TrainerMember>) | undefined;
  // The latest few payments, newest first; See All opens the rest on Payments, filtered to this member.
  const paysQ = usePaymentsList({ member: mid, limit: RECENT }, { query: { enabled: desk } });
  const pays = paysQ.data?.data.results ?? [];
  const payCount = paysQ.data?.data.count ?? 0;
  // The current plan's price, offer and what's been paid toward it, for the membership card (desk only: amounts).
  const planId = (q.data?.data as Member | undefined)?.plan?.id;
  const subQ = useSubscriptionsRetrieve(planId ?? 0, { query: { enabled: desk && !!planId } });
  // Renewals already sold, waiting for the current plan to end: the newest plans come first, so a few cover them.
  const subsQ = useSubscriptionsList({ member: mid, limit: 5 }, { query: { enabled: desk } });
  const gymDay = gymToday(role.timezone);
  const queued = (subsQ.data?.data.results ?? []).filter((s) => !s.cancelled && s.id !== planId && (s.starts ?? "") > gymDay).reverse();
  const visits = useCheckinsList({ member: mid, limit: RECENT });
  const notes = useGet<Note[]>(`/api/members/${mid}/notes/`, undefined, role.role !== "member");
  const { checkIn, outcome, busy, close } = useCheckIn();
  const [sheet, setSheet] = useState<null | "more" | "whatsapp" | { chat: Chat } | "note" | "freeze" | "login" | "edit" | "archive" | "refund" | { void: Payment } | { plan: Subscription }>(null);
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
  // What the WhatsApp messages are filled in from: a payment as a receipt reads it, a queued plan as booked.
  const paid = (p: Payment) => ({
    amount_paise: p.amount_paise, method: METHODS.find((x) => x.value === p.method)?.title ?? p.method, on: p.taken_at,
    plan: plan && p.subscription === plan.id ? plan.name : queued.find((s) => s.id === p.subscription)?.plan_name,
  });
  const booked = (s: Subscription) => ({ name: s.plan_name, starts: s.starts!, ends: s.ends!, price_paise: s.price_paise, paid_paise: s.paid_paise });
  const lastPay = pays.find((p) => !p.voided);
  const facts: ChatFacts = {
    name: m.name, code: m.code, gym: role.gym_name, today: gymDay,
    plan: plan ? { name: plan.name, starts: plan.starts, ends: plan.ends, frozen_from: plan.frozen_from, frozen_until: plan.frozen_until } : null,
    due: desk ? balance : null, paymentDue: !!m.payment_due, sub: desk ? sub : null, hasLogin: m.has_login,
    lastPayment: desk && lastPay ? paid(lastPay) : null, upcoming: queued.map(booked),
    lastVisit: visits.data?.data.results[0]?.local_date ?? null,
  };
  const chats = memberChats(facts);
  const cardChat = membershipChat(chats);
  const startChat = typeof sheet === "object" && sheet && "chat" in sheet ? sheet.chat : null;
  // The balance covers every plan: what's left once the current and booked plans' own dues are taken out is from before.
  const earlier = Math.max(0, balance - (sub ? owedOn(sub) : 0) - queued.reduce((t, s) => t + owedOn(s), 0));

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
              ? <Link className="rl-button rl-button--secondary" href={`/payments/new?member=${m.id}&back=member`}>Collect {rupees(balance)}</Link>
              : <Link className="rl-button rl-button--secondary" href={`/subscriptions/new?member=${m.id}&back=member`}>{m.status === "expired" || m.status === "expiring" || m.status === "none" ? "Renew Membership" : "New Subscription"}</Link>)}
            <div className="rl-actions__contact">
              <a className="rl-button rl-button--secondary rl-button--sm" href={`tel:+91${digits}`}><Icon as={Phone} size="sm" />Call</a>
              <button className="rl-button rl-button--secondary rl-button--sm" type="button" aria-haspopup="dialog" onClick={() => setSheet("whatsapp")}><Icon as={MessageCircle} size="sm" />WhatsApp</button>
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
                  {desk && (sub || earlier > 0) && (
                    <div className="rl-sub">
                      {sub && <PlanMoney sub={sub} />}
                      {earlier > 0 && <span><strong>{sub ? "Owed from earlier plans:" : "Payment due:"}</strong> {rupees(earlier)}</span>}
                    </div>
                  )}
                  {!desk && m.payment_due && <div className="rl-sub"><span><strong>Payment due.</strong> The front desk will collect it.</span></div>}
                  {current?.frozen_from && <div className="rl-sub"><span><strong>Frozen</strong> {day(current.frozen_from)} to {current.frozen_until ? day(current.frozen_until) : "further notice"}</span></div>}
                  {cardChat && (
                    <div style={{ marginTop: "var(--space-3)" }}>
                      <button className="rl-button rl-button--secondary rl-button--sm" type="button" aria-haspopup="dialog" onClick={() => setSheet({ chat: cardChat })}>
                        <Icon as={MessageCircle} size="sm" />Send {cardChat.title}
                      </button>
                    </div>
                  )}
                </div>
              ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No plan yet.</p></div>}
            </Section>
            {queued.length > 0 && (
              <Section title="Up next">
                <div style={{ display: "grid", gap: "var(--space-3)" }}>
                  {queued.map((s) => {
                    const inDays = daysLeft(s.starts!);
                    return (
                      <div key={s.id} className="rl-pass">
                        <div className="rl-pass__top">
                          <span className="rl-tag rl-tag--next">{inDays <= 0 ? "Starts today" : inDays === 1 ? "Starts tomorrow" : `Starts in ${inDays} days`}</span>
                          <span className="rl-pass__plan">{s.plan_name}</span>
                          {role.role === "admin" && (
                            <button className="rl-pass__link" type="button" aria-haspopup="dialog" aria-label={`Manage ${s.plan_name}`} style={LINK_RESET} onClick={() => setSheet({ plan: s })}>
                              Manage<ChevronRight className="rl-icon rl-icon--xs" strokeWidth={1.75} aria-hidden />
                            </button>
                          )}
                        </div>
                        <div className="rl-pass__dates"><span>{day(s.starts!)}</span><span>Ends {day(s.ends!)}</span></div>
                        <div className="rl-sub"><PlanMoney sub={s} /></div>
                        <div style={{ marginTop: "var(--space-3)" }}>
                          <button className="rl-button rl-button--secondary rl-button--sm" type="button" aria-haspopup="dialog" onClick={() => setSheet({ chat: nextPlanChat(facts, [booked(s)]) })}>
                            <Icon as={MessageCircle} size="sm" />Send on WhatsApp
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Section>
            )}
            <Section title="Details">
              <Details rows={[
                { icon: Phone, label: "Mobile number", value: phone(m.phone) },
                ...(desk ? [{ icon: Mail, label: "Email", value: m.email }] : []),
                { icon: MapPin, label: "Home branch", value: typeof m.home_branch === "string" ? m.home_branch : role.branches.find((b) => b.id === m.home_branch)?.name },
                ...(desk ? [{ icon: Dumbbell, label: "Trainer", value: m.trainer_name ?? "Not set" }] : []),
                { icon: Target, label: "Goal", value: m.goal || "Not set" },
                ...(desk ? [{ icon: CalendarCheck, label: "Joined", value: m.joined_on ? day(m.joined_on) : "" }, { icon: KeyRound, label: "App login", value: m.has_login ? `Signs in as @${m.username}` : "Not set" }] : []),
              ].filter((r) => r.value !== undefined)} />
            </Section>
          </div>
          <div className="rl-app__col">
            {desk && (
              <Section title="Payments" aside={payCount > 0 ? (
                <Link className="rl-link rl-link--plain" href={`/collection?member=${mid}`}><span>See All</span></Link>
              ) : undefined}>
                {paysQ.isLoading ? <SkeletonRows n={2} /> : pays.length ? (
                  <><ul className="rl-card rl-mlist rl-mlist--compact">
                    {pays.map((p, i) => (
                      <WhatsAppRow key={p.id} first={i === 0} label={`WhatsApp ${m.name} a receipt for ${rupees(p.amount_paise)}`}
                        onSend={p.voided ? undefined : () => setSheet({ chat: receiptChat(facts, paid(p)) })}>
                        <button className="rl-mrow" type="button" style={{ borderTop: 0 }} disabled={role.role !== "admin" || p.voided} onClick={() => setSheet({ void: p })}>
                          <span className="rl-chipicon" aria-hidden="true"><Icon as={UserRound} size="sm" /></span>
                          <span className="rl-row__title rl-mrow__name" style={p.voided ? { textDecoration: "line-through" } : undefined}>{rupees(p.amount_paise)} by {p.method.toUpperCase()}</span>
                          <span className="rl-row__meta rl-mrow__meta">{day(p.taken_at)} • {p.taken_by_name}{p.voided ? ` • Voided: ${p.void_reason}` : ""}</span>
                        </button>
                      </WhatsAppRow>
                    ))}
                  </ul></>
                ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No payments yet.</p></div>}
                <RefundRows member={mid} admin={role.role === "admin"} />
              </Section>
            )}
            <Section title="Recent visits" aside={role.role !== "member" && visits.data?.data.count ? (
              <Link className="rl-link rl-link--plain" href={`/visits?member=${mid}`}><span>See All</span></Link>
            ) : undefined}>
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
          {role.role === "admin" && sub && !sub.cancelled && <SheetItem icon={CalendarCog} label="Edit Membership" onClick={() => setSheet({ plan: sub })} />}
          {current && (current.frozen_from
            ? <SheetItem icon={Play} label="Unfreeze Membership" onClick={() => setSheet("freeze")} />
            : <SheetItem icon={Pause} label="Freeze Membership" onClick={() => setSheet("freeze")} />)}
          <SheetItem icon={KeyRound} label={m.has_login ? "Change App Login" : "Set Up App Login"} onClick={() => setSheet("login")} />
          {role.role === "admin" && pays.length > 0 && <SheetItem icon={Undo2} label="Refund Money" onClick={() => setSheet("refund")} />}
          {role.role === "admin" && <SheetItem icon={Trash2} label="Archive Member" onClick={() => setSheet("archive")} />}
        </ul>
      </Sheet>
      {(sheet === "whatsapp" || startChat) && (
        <WhatsAppSheet start={startChat} phone={m.phone} chats={chats} optedOut={!!m.reminders_opted_out} onClose={() => setSheet(null)} />
      )}
      <NoteSheet open={sheet === "note"} id={mid} onClose={() => setSheet(null)} />
      {current && <FreezeSheet open={sheet === "freeze"} sub={current} onClose={() => setSheet(null)} />}
      <LoginSheet open={sheet === "login"} member={m} onClose={() => setSheet(null)} />
      {desk && <EditSheet open={sheet === "edit"} member={m} onClose={() => setSheet(null)} />}
      <ArchiveSheet open={sheet === "archive"} member={m} onClose={() => setSheet(null)} />
      {sheet === "refund" && <RefundSheet member={mid} name={m.name} onClose={() => setSheet(null)} />}
      {typeof sheet === "object" && sheet && "plan" in sheet && (
        <EditMembershipSheet sub={sheet.plan} branch={typeof m.home_branch === "number" ? m.home_branch : null} onClose={() => setSheet(null)} />
      )}
      <VoidSheet payment={typeof sheet === "object" && sheet && "void" in sheet ? sheet.void : null} onClose={() => setSheet(null)} />
    </div>
  );
}

/** How a plan was paid: " by UPI" for one way, " (Cash ₹500 + UPI ₹500)" for a split. */
function paidBy(sub: Subscription) {
  const name = (m: string) => METHODS.find((x) => x.value === m)?.title ?? m;
  if (sub.paid_by.length === 1) return ` by ${name(sub.paid_by[0]!.method)}`;
  return sub.paid_by.length ? ` (${sub.paid_by.map((p) => `${name(p.method)} ${rupees(p.amount_paise)}`).join(" + ")})` : "";
}

/** How many payments and visits the profile shows; each See All has the rest. */
const RECENT = 5;

/** What's still to pay on one plan. */
const owedOn = (sub: Subscription) => Math.max(0, sub.price_paise - sub.paid_paise);

/** A link-styled button (the pass's Manage) without a button's own border and fill. */
const LINK_RESET = { border: 0, padding: 0, background: "none", fontFamily: "inherit", cursor: "pointer" } as const;

/** One plan's money, for a pass: its price and offer, what's been paid and how, refunds, and what's still due. */
function PlanMoney({ sub }: { sub: Subscription }) {
  const due = owedOn(sub);
  return (
    <>
      <span><strong>Price:</strong> {rupees(sub.price_paise)}{sub.offer_name ? ` with ${sub.offer_name} (was ${rupees(sub.list_price_paise)})` : ""}</span>
      <span><strong>Paid:</strong> {sub.paid_paise ? <>{rupees(sub.paid_paise)}{due ? ` of ${rupees(sub.price_paise)}` : " in full"}{paidBy(sub)}</> : "Nothing yet"}</span>
      {sub.refunded_paise > 0 && <span><strong>Refunded:</strong> {rupees(sub.refunded_paise)}</span>}
      {due > 0 && <span><strong>Payment due:</strong> {rupees(due)}</span>}
    </>
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

const CHAT_ICON: Record<ChatKind, typeof Pencil> = {
  payment_due: IndianRupee, renewal: CalendarClock, next_plan: CalendarCheck, payment_received: ReceiptText, membership: IdCard, frozen: Snowflake,
  missed_you: HandHeart, welcome: PartyPopper, blank: PenLine,
};

/** Pick a message (or start on one, from a card or row), check its words, then open the staff member's own WhatsApp
 *  with it typed in, ready to send. Back always leads to every message that fits. */
function WhatsAppSheet({ start, phone: to, chats, optedOut, onClose }: { start: Chat | null; phone: string; chats: Chat[]; optedOut: boolean; onClose: () => void }) {
  const [pick, setPick] = useState<Chat | null>(start);
  const [text, setText] = useState(start?.text ?? "");
  const close = () => { setPick(null); onClose(); };
  return (
    <Sheet open onClose={close} title={pick?.title ?? "Send on WhatsApp"}>
      {pick ? (
        <>
          <Field label="Message" area hint="WhatsApp opens with this typed in. Change anything before you send it.">
            {(fid) => <textarea className="rl-field__input" id={fid} rows={7} value={text} onChange={(e) => setText(e.target.value)} />}
          </Field>
          <div className="rl-sheet__actions">
            <a className="rl-button rl-button--block" href={whatsappLink(to, text.trim())} target="_blank" rel="noreferrer" onClick={close}><Icon as={MessageCircle} size="sm" />Open WhatsApp</a>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setPick(null)}>Back</button>
          </div>
        </>
      ) : (
        <>{optedOut && <p className="rl-row__meta">Reminders are off for this member. Send one only if they expect it.</p>}
        <ul className="rl-sheet__list">
          {chats.map((c) => {
            const inner = <>
              <span className="rl-chipicon"><Icon as={CHAT_ICON[c.kind]} size="sm" /></span>
              <span className="rl-sheet__text">{c.title}<span className="rl-row__meta" style={{ fontWeight: 400 }}>{c.note}</span></span>
              <ChevronRight className="rl-icon rl-icon--sm rl-chev" strokeWidth={1.75} aria-hidden />
            </>;
            return <li key={c.kind}>{c.text
              ? <button className="rl-sheet__item" type="button" onClick={() => { setPick(c); setText(c.text); }}>{inner}</button>
              : <a className="rl-sheet__item" href={whatsappLink(to)} target="_blank" rel="noreferrer" onClick={close}>{inner}</a>}</li>;
          })}
        </ul></>
      )}
    </Sheet>
  );
}

/** A list row with a WhatsApp button at its end. The line between rows moves to the item, so it runs under both;
 *  the row inside sets its own line off. */
function WhatsAppRow({ first, label, onSend, children }: { first: boolean; label: string; onSend?: () => void; children: React.ReactNode }) {
  return (
    <li style={{ display: "flex", alignItems: "center", borderTop: first ? undefined : "1px solid var(--line)" }}>
      <div style={{ flex: "1 1 auto", minWidth: 0 }}>{children}</div>
      {onSend && (
        <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label={label} title={label} aria-haspopup="dialog" style={{ marginRight: "var(--space-3)" }} onClick={onSend}>
          <Icon as={MessageCircle} size="sm" />
        </button>
      )}
    </li>
  );
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

/** A member's app login: a new one, the one they already have at another gym, or a new password or username for
 *  the one this gym gave them. A login they share with another gym is theirs to change: the API says so. */
function LoginSheet({ open, member, onClose }: { open: boolean; member: Member; onClose: () => void }) {
  const blank = { username: member.username ?? "", existing: "", pw: "" };
  const [f, setF] = useState(blank);
  const [kind, setKind] = useState<LoginKind>("new");
  const [done, setDone] = useState<LoginSet | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const a = useAction();
  const linking = !member.has_login && kind === "existing";
  const renamed = member.has_login && cleanUsername(f.username) !== member.username;
  async function go() {
    const e: Record<string, string> = {};
    if (linking && !cleanUsername(f.existing)) e.existing_username = "Enter the username they sign in with";
    if (!linking && (f.pw || !renamed) && f.pw.length < 6) e.password = "Use at least 6 characters";
    if (member.has_login && !cleanUsername(f.username)) e.username = "Enter their username";
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = linking ? { existing_username: cleanUsername(f.existing) } : { username: cleanUsername(f.username) || undefined, ...(f.pw ? { password: f.pw } : {}) };
    try { setDone((await a.run<LoginSet>(`/api/members/${member.id}/set-login/`, body))!); } catch { /* shown */ }
  }
  const close = () => { setDone(null); setF(blank); setErrs({}); a.clearError(); onClose(); };
  const err = (k: string) => errs[k] || fieldError(a.error, k);
  return (
    <Sheet open={open} onClose={close} title={done ? undefined : "App login"}>
      {done ? (
        <>
          <div className="rl-confirm"><h2 className="rl-confirm__title">Login is ready</h2>
            <p className="rl-confirm__text">{done.linked ? `${member.name} signs in as @${done.username} with their own password, as at their other gym.` : `${member.name} signs in as @${done.username}${f.pw ? " with the password you set" : ""}.`}</p></div>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={close}>Done</button></div>
        </>
      ) : (
        <>
          {member.has_login ? <p className="rl-row__meta">{member.name} signs in to the app as @{member.username}.</p> : <LoginKindChips value={kind} onChange={setKind} />}
          {linking ? (
            <ExistingLoginField value={f.existing} onChange={(v) => setF({ ...f, existing: v })} error={err("existing_username")} />
          ) : (
            <>
              <UsernameField value={f.username} onChange={(v) => setF({ ...f, username: v })} email={member.email} name={member.name} current={member.username ?? undefined}
                optional={!member.has_login} error={err("username")} />
              <Field label={member.has_login ? "New password" : "Password"} optional={renamed} error={err("password")} hint="Tell them the password. They're signed out of the app until they use it.">
                {(fid) => <input className="rl-field__input" id={fid} type="text" autoComplete="new-password" value={f.pw} onChange={(e) => { setF({ ...f, pw: e.target.value }); setErrs({}); }} />}
              </Field>
            </>
          )}
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>
            {a.busy ? "Saving…" : linking ? "Link Login" : member.has_login ? "Save Login" : "Set Up Login"}
          </button></div>
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
