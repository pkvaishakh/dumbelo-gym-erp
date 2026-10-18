/* Console Home in words: its Needs attention rows, worked out from /api/platform/summary/. */
import type { PlatformSummary } from "@/api/gen/model";

import { plural, rupees } from "./format";

export type ConsoleAttentionRow = { count: number; title: string; meta: string; href: string; dot: "" | "ring" | "ink" };

/** "Worker", "Worker and Beat", "Database, Redis and Worker". */
export function andList(names: string[]) {
  return names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/** What on the server is down and which jobs' last runs failed, in one line. */
export function serverMeta(s: PlatformSummary["server"]) {
  const parts = [];
  if (s.down.length) parts.push(`${andList(s.down.map((c) => c.label))} down`);
  if (s.failed_jobs.length) parts.push(`${andList(s.failed_jobs.map((j) => j.label))} failed`);
  return parts.join(" • ");
}

/** Needs attention, most urgent first: the server, overdue invoices, branch requests and today's failed messages.
 *  Rows at zero are left in: the card hides them, and shows its quiet line when every one is. The dots follow the
 *  design: filled for now and today, a ring for what waits, ink for money. */
export function consoleAttention(s: PlatformSummary): ConsoleAttentionRow[] {
  return [
    { count: s.server.down.length + s.server.failed_jobs.length, title: "Server problems", meta: serverMeta(s.server), href: "/console/server", dot: "" },
    {
      count: s.money.overdue_invoices, title: "Overdue invoices", dot: "ink", href: "/console/gyms?owes=overdue",
      meta: `${rupees(s.money.overdue_paise)} from ${plural(s.money.gyms_overdue, "gym")}`,
    },
    { count: s.branch_requests.waiting, title: "Branch requests", meta: "Gyms waiting for your answer", href: "/console/requests", dot: "ring" },
    { count: s.whatsapp.failed_today, title: "WhatsApp messages failed", meta: "Today, on every number", href: "/console/messages?status=failed", dot: "" },
  ];
}
