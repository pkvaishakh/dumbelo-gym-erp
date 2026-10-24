import { addDays, addMonths, differenceInCalendarDays, format, formatDistanceToNowStrict, isSameDay, parseISO, subMonths } from "date-fns";

/** ₹3,05,340 — Indian grouping, no paise unless there are some. */
export function rupees(paise: number | null | undefined) {
  const p = paise ?? 0;
  const r = p / 100;
  return "₹" + r.toLocaleString("en-IN", { minimumFractionDigits: p % 100 ? 2 : 0, maximumFractionDigits: p % 100 ? 2 : 0 });
}

export function toPaise(rupeesText: string | number) {
  const n = typeof rupeesText === "number" ? rupeesText : Number(String(rupeesText).replace(/[^\d.]/g, ""));
  return Number.isFinite(n) ? Math.round(n * 100) : 0;
}

export const d = (iso: string) => parseISO(iso);
export const day = (iso: string) => format(parseISO(iso), "d MMM yyyy");
export const dayShort = (iso: string) => format(parseISO(iso), "d MMM");
export const isoDate = (date: Date) => format(date, "yyyy-MM-dd");

/** A plan's last day from its first, as the API works it out (clock.plan_end). In calendar months (`monthDays` 0)
 *  1 month from 14 Oct ends 13 Nov, and from 31 Jan ends 27 Feb (no 31 Feb, so 28 Feb less a day); at a gym whose
 *  month is 28 days, 1 month from 14 Oct ends 10 Nov. */
export function planEnd(starts: string, months: number | undefined, monthDays: number) {
  const s = parseISO(starts);
  return isoDate(monthDays ? addDays(s, (months || 3) * monthDays - 1) : addDays(addMonths(s, months || 3), -1));
}
/** The gym's own day ("2026-10-18") in its time zone: what the API calls today, wherever this device is set. */
export function gymToday(timeZone: string, now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}
/** A moment's time of day in the gym's time zone, as a time input holds it ("06:05"): a check-in's Change Time. */
export function gymClock(iso: string, timeZone: string) {
  return new Intl.DateTimeFormat("en-GB", { timeZone, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(iso));
}
export const ago = (iso: string) => formatDistanceToNowStrict(parseISO(iso), { addSuffix: true });
/** When a device last spoke to us: "2 hours ago", or "Never" for one that never has. */
export const seen = (iso: string | null | undefined) => (iso ? ago(iso) : "Never");
export const daysLeft = (iso: string) => differenceInCalendarDays(parseISO(iso), new Date());
/** A plan's days, its first and last both counted: how many have gone before `today` and how many are left with it. */
export function planDays(starts: string, ends: string, today: string) {
  const total = differenceInCalendarDays(parseISO(ends), parseISO(starts)) + 1;
  const used = Math.min(total, Math.max(0, differenceInCalendarDays(parseISO(today), parseISO(starts))));
  return { total, used, left: total - used };
}
/** The clock time something runs out: "6:00 PM" today, "6:00 PM on 18 Oct" any other day. */
export function until(iso: string, now = new Date()) {
  const end = parseISO(iso);
  const time = format(end, "h:mm a");
  return isSameDay(end, now) ? time : `${time} on ${format(end, "d MMM")}`;
}

/** "6:30 AM" from "06:30:00" */
export function clock(t: string | null | undefined) {
  if (!t) return "";
  const [h, m] = t.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  const hh = h % 12 || 12;
  return m ? `${hh}:${String(m).padStart(2, "0")} ${suffix}` : `${hh} ${suffix}`;
}

/** "5–10 AM", "5 PM–10 PM" → compact like the design: "12–4 PM" */
export function span(starts: string, ends: string) {
  const a = clock(starts), b = clock(ends);
  const [an, as] = a.split(" "), [, bs] = b.split(" ");
  return as === bs ? `${an}–${b}` : `${a}–${b}`;
}

export function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]!.toUpperCase()).join("");
}

export function greeting(name: string, wave = true) {
  const h = new Date().getHours();
  const part = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  return `${part}, ${name.split(" ")[0]}${wave ? " 👋" : ""}`;
}

export function plural(n: number, one: string, many = one + "s") {
  return `${n.toLocaleString("en-IN")} ${n === 1 ? one : many}`;
}

/** +91 98000 00001 */
export function phone(p: string | null | undefined) {
  if (!p) return "Not added";
  const m = p.replace(/\D/g, "").slice(-10);
  return m.length === 10 ? `+91 ${m.slice(0, 5)} ${m.slice(5)}` : p;
}

export const STATUS_LABEL: Record<string, string> = {
  active: "Active", expiring: "Expiring", due: "Payment due", frozen: "Frozen", expired: "Expired", none: "No plan",
  off: "Off", // a branch, staff member or device that has been switched off
};

/** Axis and cap labels: "₹850", "₹48.6k", "₹1.2L", "₹3.4Cr" (Indian units, one decimal at most). */
export function rupeesShort(paise: number) {
  const r = paise / 100;
  const one = (n: number) => String(Math.round(n * 10) / 10);
  if (r >= 1e7) return `₹${one(r / 1e7)}Cr`;
  if (r >= 1e5) return `₹${one(r / 1e5)}L`;
  if (r >= 1e3) return `₹${one(r / 1e3)}k`;
  return `₹${Math.round(r)}`;
}

/** "28 Sep to 4 Oct"; years appear when the range isn't all in this year. */
export function rangeLabel(from: string, to: string, now = new Date()) {
  const a = parseISO(from), b = parseISO(to);
  const thisYear = a.getFullYear() === now.getFullYear() && b.getFullYear() === now.getFullYear();
  const f = thisYear ? "d MMM" : "d MMM yyyy";
  return from === to ? format(a, f) : `${format(a, f)} to ${format(b, f)}`;
}

/** A figure against the same number of days just before: "+9% vs previous 7 days", "+9% vs the day before". */
export function trend(now: number, before: number, days: number): { dir: "up" | "down" | "flat"; text: string } {
  const prior = days === 1 ? "the day before" : `previous ${plural(days, "day")}`;
  const vs = `vs ${prior}`;
  if (now === before) return { dir: "flat", text: `Same as ${prior}` };
  if (before === 0) return { dir: "up", text: `Up from 0 ${vs}` };
  const pct = Math.round(((now - before) / before) * 100);
  const dir = now > before ? "up" : "down";
  return { dir, text: `${pct > 0 ? "+" : pct === 0 ? (dir === "up" ? "+" : "-") : ""}${pct}% ${vs}` };
}

/** "October 2026" from "2026-10-01" or "2026-10". */
export const monthLabel = (iso: string) => format(parseISO(iso.length === 7 ? `${iso}-01` : iso), "MMMM yyyy");

/** This month and the `n - 1` before it, newest first, as month chips: "This month", "Sep 2026". */
export function recentMonths(n = 6, now = new Date()) {
  return Array.from({ length: n }, (_, i) => {
    const m = subMonths(now, i);
    return { value: format(m, "yyyy-MM"), label: i === 0 ? "This month" : format(m, "MMM yyyy") };
  });
}

export const EXPENSE_CATEGORY: Record<string, string> = {
  rent: "Rent", salaries: "Salaries", utilities: "Utilities", equipment: "Equipment", maintenance: "Maintenance", supplies: "Supplies", marketing: "Marketing", other: "Other",
};
export const PAY_METHOD: Record<string, string> = { cash: "Cash", upi: "UPI", card: "Card", bank: "Bank transfer" };
export const FREQUENCY: Record<string, string> = { weekly: "Every week", monthly: "Every month", quarterly: "Every 3 months", yearly: "Every year" };
export const PAY_TYPE: Record<string, string> = {
  fixed: "Fixed monthly salary", attendance: "Monthly salary, by days present", hourly: "By the hour", daily: "By the day",
};
/** The pay type in a list row's few words. */
export const PAY_TYPE_SHORT: Record<string, string> = { fixed: "Fixed", attendance: "By attendance", hourly: "By the hour", daily: "By the day" };
/** What a salary's rate is per, for "₹800 a day". */
export const RATE_PER: Record<string, string> = { fixed: "a month", attendance: "a month", hourly: "an hour", daily: "a day" };
export const LINE_KIND: Record<string, string> = { allowance: "Allowance", incentive: "Incentive", referral: "Referral bonus", deduction: "Deduction" };

/** What a money move did, in the words on its row: "Cash to bank", "Deposit". */
/** A cash count against what the drawer should hold: "₹200 short", "₹50 over", or "Matches". */
export function countDifference(paise: number) {
  return paise === 0 ? "Matches" : paise < 0 ? `${rupees(-paise)} short` : `${rupees(paise)} over`;
}

export function moveLabel(m: { kind: string; from_kind?: string | null; to_kind?: string | null }) {
  if (m.kind === "deposit") return "Deposit";
  if (m.kind === "withdrawal") return "Withdrawal";
  if (m.from_kind === "cash") return m.to_kind === "cash" ? "Cash between branches" : "Cash to bank";
  return m.to_kind === "cash" ? "Bank to cash" : "Bank to bank";
}

/** "•• 5678": enough of an account number to tell two accounts apart on a list. */
export const lastDigits = (n: string | null | undefined) => (n ? `•• ${n.slice(-4)}` : "");

/** A gym's short name from its name, as New Gym suggests it: "Iron House, Kochi" → "iron-house-kochi". The API's
 *  rule: 3 to 40 lowercase letters, numbers and dashes, starting and ending with a letter or number. */
export function slugify(name: string) {
  return name.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40).replace(/^-+|-+$/g, "");
}
export const SLUG_RULE = /^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$/;

export const GYM_STATUS: Record<string, { label: string; badge: string }> = {
  active: { label: "Active", badge: "active" },
  trial: { label: "Trial", badge: "frozen" },
  suspended: { label: "Suspended", badge: "expired" },
};

/** "1st", "22nd": the day of the month a gym's Dumbelo invoice is written. */
export function ordinal(n: number) {
  const tens = n % 100;
  const end = tens >= 11 && tens <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th";
  return `${n}${end}`;
}

/** "2 of 3 branches": how much of a gym's Dumbelo plan is in use. */
export const branchesOf = (inUse: number, quota: number) => `${inUse} of ${plural(quota, "branch", "branches")}`;

export const WHATSAPP_MODE: Record<string, { label: string; note: string }> = {
  shared: { label: "Dumbelo's number", note: "Messages go from Dumbelo's WhatsApp number, billed by the message" },
  own: { label: "The gym's own number", note: "Messages go from the gym's own WhatsApp account; it pays Meta itself" },
  off: { label: "Off", note: "No WhatsApp messages are sent" },
};

/** Whether a WhatsApp number works, as a badge: an account's status, or a gym's ("not set up", "off"). */
/** A demo request from the landing page, as the Console's Leads shows it. New ones wait for a call. */
export const LEAD_STATUS: Record<string, { label: string; badge: string }> = {
  new: { label: "New", badge: "due" },
  contacted: { label: "Contacted", badge: "frozen" },
  won: { label: "Signed up", badge: "active" },
  lost: { label: "Not now", badge: "off" },
};

export const WHATSAPP_STATUS: Record<string, { label: string; badge: string }> = {
  new: { label: "Not checked yet", badge: "frozen" },
  working: { label: "Working", badge: "active" },
  failing: { label: "Not working", badge: "expired" },
  not_set_up: { label: "Not set up yet", badge: "expiring" },
  off: { label: "Off", badge: "off" },
};

/** A WhatsApp template's status, as Meta's dashboard shows it. */
export const TEMPLATE_STATUS: Record<string, { label: string; badge: string }> = {
  pending: { label: "Waiting for Meta", badge: "frozen" },
  approved: { label: "Approved", badge: "active" },
  rejected: { label: "Rejected", badge: "expired" },
  paused: { label: "Paused", badge: "expiring" },
  disabled: { label: "Disabled", badge: "off" },
};

export const BRANCH_ASK_STATUS: Record<string, { label: string; badge: string }> = {
  asked: { label: "Waiting", badge: "frozen" },
  approved: { label: "Approved", badge: "active" },
  declined: { label: "Declined", badge: "expired" },
};

/** A Dumbelo invoice's state as a badge. An open invoice past its due day is "Overdue". */
export const INVOICE_STATUS: Record<string, { label: string; badge: string }> = {
  open: { label: "To pay", badge: "expiring" },
  overdue: { label: "Overdue", badge: "expired" },
  paid: { label: "Paid", badge: "active" },
  void: { label: "Void", badge: "off" },
};
export const invoiceState = (inv: { status: string; overdue: boolean }) => (inv.status === "open" && inv.overdue ? "overdue" : inv.status);

/** How a gym paid Dumbelo. */
export const DUMBELO_PAY_METHOD: Record<string, string> = { bank: "Bank transfer", upi: "UPI", cheque: "Cheque", card: "Card", cash: "Cash" };

/** The Console's Server screen: a check's state, and a job run's. */
export const SERVER_STATE: Record<string, { label: string; badge: string }> = {
  up: { label: "Up", badge: "active" },
  down: { label: "Down", badge: "expired" },
  off: { label: "Not used here", badge: "frozen" },
  unknown: { label: "Can't tell", badge: "expiring" },
};
export const RUN_STATE: Record<string, { label: string; badge: string }> = {
  queued: { label: "Waiting", badge: "frozen" },
  running: { label: "Running", badge: "expiring" },
  done: { label: "Done", badge: "active" },
  failed: { label: "Failed", badge: "expired" },
};

/** How long a job run took: "under a second", "12 seconds", "3 min 5 s". */
export function took(seconds: number) {
  if (seconds < 1) return "under a second";
  const all = Math.round(seconds);
  if (all < 60) return plural(all, "second");
  const m = Math.floor(all / 60), s = all % 60;
  return s ? `${m} min ${s} s` : `${m} min`;
}

/** A WhatsApp message's state as a badge, in the Console's log. */
export const MESSAGE_STATUS: Record<string, { label: string; badge: string }> = {
  queued: { label: "Sending", badge: "expiring" },
  sent: { label: "Sent", badge: "frozen" },
  delivered: { label: "Delivered", badge: "active" },
  read: { label: "Read", badge: "active" },
  failed: { label: "Failed", badge: "expired" },
};

/** "18 Oct 2026, 9:05 AM" on this device's clock. */
export const dayTime = (iso: string) => format(parseISO(iso), "d MMM yyyy, h:mm a");
