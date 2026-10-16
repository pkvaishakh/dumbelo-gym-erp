import { differenceInCalendarDays, format, formatDistanceToNowStrict, parseISO } from "date-fns";

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
export const ago = (iso: string) => formatDistanceToNowStrict(parseISO(iso), { addSuffix: true });
/** When a device last spoke to us: "2 hours ago", or "Never" for one that never has. */
export const seen = (iso: string | null | undefined) => (iso ? ago(iso) : "Never");
export const daysLeft = (iso: string) => differenceInCalendarDays(parseISO(iso), new Date());

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
