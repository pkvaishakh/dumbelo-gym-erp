/* The WhatsApp messages the desk or a trainer can send a member from their profile: picked from a list, the words
   filled in from what the page knows, then opened in the staff member's own WhatsApp to edit and send. These go
   from their phone, not Dumbelo's number, so nothing here is logged or billed. */
import { differenceInCalendarDays, parseISO } from "date-fns";

import { day, rupees } from "./format";

export type ChatKind = "payment_due" | "renewal" | "next_plan" | "payment_received" | "membership" | "frozen" | "missed_you" | "welcome" | "blank";

export type Chat = { kind: ChatKind; title: string; note: string; text: string };

export type ChatFacts = {
  name: string;
  code?: string;
  gym: string;
  /** The gym's day, "2026-10-24" */
  today: string;
  plan: { name: string; starts?: string | null; ends: string; frozen_from?: string | null; frozen_until?: string | null } | null;
  /** What they owe in paise, or null for a reader who never sees amounts (a trainer) */
  due: number | null;
  /** That they owe something, for a reader who can't see how much */
  paymentDue?: boolean;
  /** The current plan's price and what's been paid toward it (the desk only) */
  sub?: { price_paise: number; paid_paise: number } | null;
  /** Their latest payment that stands (the desk only); `plan` names the plan it went toward */
  lastPayment?: { amount_paise: number; method: string; on: string; plan?: string } | null;
  /** The day of their latest visit */
  lastVisit?: string | null;
  /** Plans already sold and waiting for the current one to end, soonest first (the desk only): no need to ask them
   *  to renew, and they're told what's booked */
  upcoming?: { name: string; starts: string; ends: string; price_paise: number; paid_paise: number }[];
  hasLogin?: boolean;
};

/** Days a member can go without a visit before "We Miss You" is offered. */
export const MISSED_AFTER = 7;
/** How close to its end a plan has to be for the renewal reminder. */
export const RENEW_WITHIN = 7;

const firstName = (name: string) => name.trim().split(/\s+/)[0] || name;
const between = (from: string, to: string) => differenceInCalendarDays(parseISO(to), parseISO(from));

/** The messages that fit this member today, the most pressing first, ending with a blank one. */
export function memberChats(f: ChatFacts): Chat[] {
  const hi = `Hi ${firstName(f.name)}`;
  const plan = f.plan;
  const yours = plan ? `your ${plan.name} plan` : "your membership";
  const left = plan ? between(f.today, plan.ends) : null;  // 0 the day it ends, below 0 once it has
  const running = left !== null && left >= 0;
  const owes = f.due !== null ? f.due > 0 : !!f.paymentDue;
  const upcoming = f.upcoming ?? [];
  const amounts = f.due !== null;
  const out: Chat[] = [];

  if (owes) {
    // The balance covers every plan that isn't cancelled: name the plan only when the money is all on one of them.
    const owing = [...(f.sub && plan && f.sub.paid_paise < f.sub.price_paise ? [plan.name] : []), ...upcoming.filter((u) => u.paid_paise < u.price_paise).map((u) => u.name)];
    const forWhat = !upcoming.length ? yours : owing.length === 1 ? `your ${owing[0]} plan` : "your membership";
    out.push({
      kind: "payment_due", title: "Payment Due Reminder", note: amounts ? `${rupees(f.due)} owed` : "Without the amount",
      text: `${hi}, ${amounts ? `${rupees(f.due)} is` : "a payment is"} still due for ${forWhat} at ${f.gym}. You can pay at the front desk on your next visit. Thank you!`,
    });
  }

  if (upcoming.length) out.push(nextPlanChat(f, upcoming));

  if (plan && left !== null && !upcoming.length && left <= RENEW_WITHIN) {
    const when = left < 0 ? null : left === 0 ? "today" : left === 1 ? "tomorrow" : `in ${left} days, on ${day(plan.ends)}`;
    out.push({
      kind: "renewal", title: "Renewal Reminder", note: left < 0 ? `Ended ${day(plan.ends)}` : left === 0 ? "Ends today" : `Ends ${day(plan.ends)}`,
      text: when
        ? `${hi}, ${yours} at ${f.gym} ends ${when}. Renew it at the front desk to keep training without a break.`
        : `${hi}, ${yours} at ${f.gym} ended on ${day(plan.ends)}. Renew it at the front desk to start training again. We'd love to see you back!`,
    });
  }

  if (f.lastPayment) out.push(receiptChat(f, f.lastPayment));

  if (plan && running) {
    const lines = [`${hi}, here are your membership details at ${f.gym}.`, `Plan: ${plan.name}`];
    lines.push(plan.starts ? `From ${day(plan.starts)} to ${day(plan.ends)}` : `Ends ${day(plan.ends)}`);
    if (amounts && f.sub) {
      lines.push(`Price: ${rupees(f.sub.price_paise)}`, `Paid: ${rupees(f.sub.paid_paise)}`);
      if (f.sub.paid_paise < f.sub.price_paise) lines.push(`Due: ${rupees(f.sub.price_paise - f.sub.paid_paise)}`);
    } else if (f.due) lines.push(`Due: ${rupees(f.due)}`);
    if (upcoming.length) lines.push(`Next: ${upcoming[0]!.name}, from ${day(upcoming[0]!.starts)}`);
    if (f.code) lines.push(`Member code: ${f.code}`);
    out.push({ kind: "membership", title: "Membership Details", note: `${plan.name}, till ${day(plan.ends)}`, text: lines.join("\n") });
  }

  if (plan?.frozen_from) {
    const until = plan.frozen_until ? day(plan.frozen_until) : "further notice";
    out.push({
      kind: "frozen", title: "Freeze Confirmation", note: `Frozen till ${until}`,
      text: `${hi}, ${yours} at ${f.gym} is frozen from ${day(plan.frozen_from)} to ${until}. `
        + (plan.frozen_until ? `The days frozen are added to the end, so it now ends on ${day(plan.ends)}.` : "The days frozen are added to the end of your plan."),
    });
  }

  const away = f.lastVisit ? between(f.lastVisit, f.today) : null;
  if (plan && running && !plan.frozen_from && (away === null ? !plan.starts || between(plan.starts, f.today) >= MISSED_AFTER : away >= MISSED_AFTER)) {
    out.push({
      kind: "missed_you", title: "We Miss You", note: f.lastVisit ? `Last visit ${day(f.lastVisit)}` : "No visits yet",
      text: `${hi}, we haven't seen you at ${f.gym} ${f.lastVisit ? `since ${day(f.lastVisit)}` : "yet"}. Everything okay? Your ${plan.name} plan runs till ${day(plan.ends)}, so come in for a workout this week!`,
    });
  }

  out.push({
    kind: "welcome", title: "Welcome Message", note: "How to check in, and their member code",
    text: [
      `${hi}, welcome to ${f.gym}!`,
      f.code && `Your member code is ${f.code}.`,
      plan && running && (plan.starts ? `Your ${plan.name} plan runs from ${day(plan.starts)} to ${day(plan.ends)}.` : `Your ${plan.name} plan runs till ${day(plan.ends)}.`),
      f.hasLogin
        ? "Check in at the front desk, or scan the QR code on the wall with the app. Sign in to the app with this mobile number to see your plan and visits."
        : "Check in at the front desk when you come in.",
    ].filter(Boolean).join(" "),
  });

  out.push({ kind: "blank", title: "Write Your Own", note: "An empty message", text: "" });
  return out;
}

type Upcoming = NonNullable<ChatFacts["upcoming"]>[number];
type Paid = NonNullable<ChatFacts["lastPayment"]>;

/** What's booked after the current plan: one plan, or several a line each. Amounts only for a reader who sees them. */
export function nextPlanChat(f: ChatFacts, plans: Upcoming[]): Chat {
  const hi = `Hi ${firstName(f.name)}`, amounts = f.due !== null, next = plans[0]!;
  const money = (u: Upcoming) => u.paid_paise >= u.price_paise ? "paid in full" : `${rupees(u.price_paise - u.paid_paise)} of ${rupees(u.price_paise)} due`;
  const seamless = !!f.plan && between(f.today, f.plan.ends) >= 0 && between(f.plan.ends, next.starts) === 1;
  const text = plans.length > 1
    ? [`${hi}, your next plans at ${f.gym} are booked:`,
      ...plans.map((u) => `${u.name}: ${day(u.starts)} to ${day(u.ends)}${amounts ? `, ${money(u)}` : ""}`),
      ...(seamless ? ["The first starts right after your current plan ends, so there's no break."] : [])].join("\n")
    : `${hi}, your next plan at ${f.gym} is booked: ${next.name}, from ${day(next.starts)} to ${day(next.ends)}.`
      + (seamless ? " It starts right after your current plan ends, so there's no break." : "")
      + (!amounts ? "" : next.paid_paise >= next.price_paise ? " It's paid in full. Thank you!" : ` ${rupees(next.price_paise - next.paid_paise)} of ${rupees(next.price_paise)} is still due.`);
  return {
    kind: "next_plan", title: "Next Plan Confirmation", text,
    note: plans.length > 1 ? `${plans.length} plans, from ${day(next.starts)}` : `${next.name}, from ${day(next.starts)}`,
  };
}

/** A receipt for one payment, and what they still owe today. */
export function receiptChat(f: ChatFacts, pay: Paid): Chat {
  const still = f.due ? ` ${rupees(f.due)} is still due.` : "";
  return {
    kind: "payment_received", title: "Payment Receipt", note: `${rupees(pay.amount_paise)} by ${pay.method}, ${day(pay.on)}`,
    text: `Hi ${firstName(f.name)}, we've received ${rupees(pay.amount_paise)} by ${pay.method} on ${day(pay.on)} for ${pay.plan ? `your ${pay.plan} plan` : "your membership"} at ${f.gym}. Thank you!${still}`,
  };
}

/** The message the membership card offers: renew when it's ending, the freeze while frozen, else its details. */
export function membershipChat(chats: Chat[]): Chat | undefined {
  for (const kind of ["renewal", "frozen", "membership", "next_plan"] as const) {
    const c = chats.find((x) => x.kind === kind);
    if (c) return c;
  }
}

/** A link that opens WhatsApp on a chat with this Indian mobile number, the text typed in, ready to send. */
export function whatsappLink(phone: string, text = "") {
  const to = `91${phone.replace(/\D/g, "").slice(-10)}`;
  return `https://wa.me/${to}${text ? `?text=${encodeURIComponent(text)}` : ""}`;
}
