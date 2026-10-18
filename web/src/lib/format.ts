import { differenceInCalendarDays, format, formatDistanceToNowStrict, isSameDay, parseISO, subMonths } from "date-fns";

/** ₹3,05,340 — Indian grouping, no paise unless there are some. */
export function rupees(paise: number | null | undefined) {
  const p = paise ?? 0;
  const r = p / 100;
  return "₹" + r.toLocaleString("en-IN", { maximumFractionDigits: p % 100 ? 2 : 0 });
}

export function toPaise(rupeesText: string | number) {
  const n = typeof rupeesText === "number" ? rupeesText : Number(String(rupeesText).replace(/[^\d.]/g, ""));
  return Number.isFinite(n) ? Math.round(n * 100) : 0;
}

export const d = (iso: string) => parseISO(iso);
export const day = (iso: string) => format(parseISO(iso), "d MMM yyyy");
export const dayShort = (iso: string) => format(parseISO(iso), "d MMM");
export const isoDate = (date: Date) => format(date, "yyyy-MM-dd");
/** The gym's own day ("2026-10-18") in its time zone: what the API calls today, wherever this device is set. */
export function gymToday(timeZone: string, now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}
export const ago = (iso: string) => formatDistanceToNowStrict(parseISO(iso), { addSuffix: true });
/** When a device last spoke to us: "2 hours ago", or "Never" for one that never has. */
export const seen = (iso: string | null | undefined) => (iso ? ago(iso) : "Never");
export const daysLeft = (iso: string) => differenceInCalendarDays(parseISO(iso), new Date());
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

/** A figure against the same number of days just before: "+9% vs previous 7 days". */
export function trend(now: number, before: number, days: number): { dir: "up" | "down" | "flat"; text: string } {
  const vs = `vs previous ${plural(days, "day")}`;
  if (now === before) return { dir: "flat", text: `Same as previous ${plural(days, "day")}` };
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
