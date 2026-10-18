/* When each WhatsApp message goes out, in the words a gym's admin or a Rackline admin reads. The times themselves
   come from the API (Rackline's, or a gym's own); this only says them. */
import type { Rule } from "@/api/gen/model";

/** Every whole hour of a day, for an hour picker. */
export const HOURS = Array.from({ length: 24 }, (_, h) => h);
/** Days ahead offered for the plan ending message: up to 3 picked. */
export const DAY_CHOICES = [1, 2, 3, 5, 7, 10, 14, 30];
export const MAX_WARNINGS = 3;

/** "6 AM", "12 PM", "12 AM": a whole hour on a 24-hour clock. */
export function hourLabel(h: number) {
  return `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`;
}

/** "7 and 3 days", "1 day", "7 days and 1 day": furthest first. */
export function daysLabel(days: readonly number[]) {
  const all = [...new Set(days)].sort((a, b) => b - a);
  if (all.length <= 1) return all.length ? `${all[0]} ${all[0] === 1 ? "day" : "days"}` : "";
  const head = all.slice(0, -1).join(", "), last = all[all.length - 1];
  return last === 1 ? `${head} days and 1 day` : `${head} and ${last} days`;
}

const AS_IT_HAPPENS: Record<string, string> = {
  payment_received: "When the desk records a payment",
  task_assigned: "When an admin gives them a task",
  rackline_payment_received: "When Rackline records a payment",
};

/** When a message goes out: "7 and 3 days before a plan ends, at 6 AM", or what sends it. */
export function whenLabel(r: Pick<Rule, "kind" | "hour" | "days_ahead">) {
  if (r.hour == null) return AS_IT_HAPPENS[r.kind] ?? "When it happens";
  const at = hourLabel(r.hour);
  switch (r.kind) {
    case "plan_ending": return `${daysLabel(r.days_ahead ?? [])} before a plan ends, at ${at}`;
    case "plan_ends_today": return `The day a plan ends, at ${at}`;
    case "payment_due": return `Each day money is owed, at ${at}`;
    case "rackline_invoice_due": return `3 days before an invoice is due, then 1 and 7 days after, at ${at}`;
    default: return `At ${at}`;
  }
}

/** Who each message goes to. */
export const MESSAGE_TO: Record<string, string> = {
  plan_ending: "The member", plan_ends_today: "The member", payment_due: "The member", payment_received: "The member",
  task_assigned: "The trainer or receptionist", rackline_invoice_due: "The gym's owner", rackline_payment_received: "The gym's owner",
};
