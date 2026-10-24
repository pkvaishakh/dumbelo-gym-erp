/* The periods a list can be narrowed to, and the days each one covers, in the gym's day. Shared by Payments and a
   member's Visits. */
import { parseISO, startOfMonth, startOfYear, subDays } from "date-fns";

import { isoDate } from "./format";

export type Period = "today" | "yesterday" | "7d" | "month" | "custom" | "all" | "90d" | "year";

/** The day's money and the days around it (Payments). */
export const PERIODS: { value: Period; label: string }[] = [
  { value: "today", label: "Today" }, { value: "yesterday", label: "Yesterday" }, { value: "7d", label: "7 days" },
  { value: "month", label: "This month" }, { value: "custom", label: "Custom" },
];

/** One person's history goes back as far as it does, so its periods start from all of it. */
export const HISTORY_PERIODS: { value: Period; label: string }[] = [
  { value: "all", label: "All time" }, { value: "month", label: "This month" }, { value: "90d", label: "90 days" },
  { value: "year", label: "This year" }, { value: "custom", label: "Custom" },
];

/** The first and last day a period covers ("" for all time); "custom" takes the days asked for, `to` falling back to
 *  `from` and both to today. */
export function rangeOf(period: Period, today: string, from: string | null, to: string | null): [string, string] {
  const t = parseISO(today);
  if (period === "all") return ["", ""];
  if (period === "90d") return [isoDate(subDays(t, 89)), today];
  if (period === "year") return [isoDate(startOfYear(t)), today];
  if (period === "yesterday") { const y = isoDate(subDays(t, 1)); return [y, y]; }
  if (period === "7d") return [isoDate(subDays(t, 6)), today];
  if (period === "month") return [isoDate(startOfMonth(t)), today];
  if (period === "custom") return [from || today, to || from || today];
  return [today, today];
}

/** A history period from the address, all time when it's missing or one the list doesn't offer. */
export function historyPeriod(asked: string | null): Period {
  return HISTORY_PERIODS.find((p) => p.value === asked)?.value ?? "all";
}
