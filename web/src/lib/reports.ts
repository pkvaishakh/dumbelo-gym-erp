/* Reports: the categories, the periods and the range rules. The API checks the same rules (api/apps/reports/period.py). */
import { addDays, addMonths, format, parseISO, startOfMonth } from "date-fns";

import { dayShort, rupees } from "./format";

/** The longest range a report covers, in calendar months: the API's MAX_MONTHS. */
export const MAX_MONTHS = 3;

export const CATEGORIES = [
  { slug: "revenue", name: "Revenue" },
  { slug: "expenses", name: "Expenses" },
  { slug: "money", name: "Cash and bank" },
  { slug: "members", name: "Members" },
  { slug: "attendance", name: "Attendance" },
  { slug: "tasks", name: "Tasks" },
] as const;
export type Category = (typeof CATEGORIES)[number]["slug"];
export const isCategory = (s: string): s is Category => CATEGORIES.some((c) => c.slug === s);
export const categoryName = (slug: Category) => CATEGORIES.find((c) => c.slug === slug)!.name;

export type Period = "7d" | "30d" | "month" | "3m" | "custom";
export const PERIODS: { value: Period; label: string }[] = [
  { value: "7d", label: "7 days" }, { value: "30d", label: "30 days" }, { value: "month", label: "This month" },
  { value: "3m", label: "3 months" }, { value: "custom", label: "Custom" },
];
export const isPeriod = (s: string | null): s is Period => PERIODS.some((p) => p.value === s);

const iso = (d: Date) => format(d, "yyyy-MM-dd");
const isDay = (s: string | null | undefined): s is string => !!s && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(parseISO(s).getTime());

/** The first day a range ending on `to` may start: the day after the same date 3 months before (19 Jul for 18 Oct).
 *  date-fns clamps a short month's end the way the API does: 31 May goes back to 28 Feb, so from 1 Mar. */
export function earliest(to: string) {
  return iso(addDays(addMonths(parseISO(to), -MAX_MONTHS), 1));
}

/** The first and last day a period covers, ending on the gym's `today` unless the range is custom. */
export function rangeOf(period: Period, today: string, from?: string | null, to?: string | null): [string, string] {
  const t = parseISO(today);
  if (period === "30d") return [iso(addDays(t, -29)), today];
  if (period === "month") return [iso(startOfMonth(t)), today];
  if (period === "3m") return [earliest(today), today];
  if (period === "custom") return [isDay(from) ? from : iso(addDays(t, -6)), isDay(to) ? to : today];
  return [iso(addDays(t, -6)), today];
}

/** What's wrong with a custom range, in the API's words and on the field it names, or null when it's fine. */
export function rangeError(from: string, to: string, today: string): { field: "from" | "to"; message: string } | null {
  if (to > today) return { field: "to", message: "Pick today or an earlier day" };
  if (from > to) return { field: "from", message: "Pick a start date on or before the end date" };
  if (from < earliest(to)) return { field: "from", message: `Pick a range of ${MAX_MONTHS} months or less` };
  return null;
}

/** A balance against what it held before the first day: "+₹12,000 since 12 Oct". */
export function changeSince(now: number, before: number, from: string): { dir: "up" | "down" | "flat"; text: string } {
  if (now === before) return { dir: "flat", text: `Same as before ${dayShort(from)}` };
  const dir = now > before ? "up" : "down";
  return { dir, text: `${dir === "up" ? "+" : "−"}${rupees(Math.abs(now - before))} since ${dayShort(from)}` };
}
