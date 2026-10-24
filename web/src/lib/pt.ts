/** Personal training in numbers: sessions left, and whether it has ended or is near its end, by the API's rules
 *  (Subscription.is_over, is_ending). */
import { addDays, parseISO } from "date-fns";

import { isoDate, planDays, plural } from "./format";

const EXPIRING_DAYS = 7;
const FEW_SESSIONS_LEFT = 2;

export type PTLike = { starts: string; ends: string; sessions: number; sessions_used: number; frozen_from?: string | null; frozen_until?: string | null };

/** Where personal training stands on `today` (the gym's day): sessions left and a status for its badge. */
export function ptState(pt: PTLike, today: string) {
  const left = Math.max(0, pt.sessions - pt.sessions_used);
  const frozen = !!pt.frozen_from && pt.frozen_from <= today && (!pt.frozen_until || today <= pt.frozen_until);
  const over = pt.ends < today || left === 0;
  const ending = pt.ends <= isoDate(addDays(parseISO(today), EXPIRING_DAYS)) || left <= FEW_SESSIONS_LEFT;
  const status = frozen ? "frozen" : over ? "expired" : ending ? "expiring" : "active";
  return { left, over, status };
}

/** "8 of 12 sessions used". */
export const sessionsUsed = (pt: PTLike) => `${pt.sessions_used} of ${pt.sessions} sessions used`;

/** The body parts a session offers first, as the API spells them (PTSession.BODY_PARTS). Trainers add any other. */
export const BODY_PARTS = ["Chest", "Back", "Legs", "Shoulders", "Triceps", "Biceps", "Cardio"];

/** `parts` with `part` added once: spaces tidied, the usual ones spelt as BODY_PARTS has them, any other as typed. */
export function addPart(parts: readonly string[], part: string) {
  const tidy = part.trim().replace(/\s+/g, " ");
  if (!tidy || parts.some((p) => p.toLowerCase() === tidy.toLowerCase())) return [...parts];
  return [...parts, BODY_PARTS.find((p) => p.toLowerCase() === tidy.toLowerCase()) ?? tidy];
}

/** The parts to pick from: the usual ones, then others this plan's sessions used, then any already picked. */
export const partChoices = (...more: (readonly string[])[]) => more.flat().reduce<string[]>(addPart, BODY_PARTS);

/** "Chest, Back and Cardio". */
export function partsLabel(parts: readonly string[]) {
  return parts.length < 2 ? parts.join("") : `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
}

/** How often each body part was worked across `sessions`, most first; ties in BODY_PARTS order, then by name. */
export function partCounts(sessions: readonly { body_parts: readonly string[] }[]) {
  const n = new Map<string, number>();
  for (const s of sessions) for (const p of s.body_parts) n.set(p, (n.get(p) ?? 0) + 1);
  const rank = (p: string) => { const i = BODY_PARTS.indexOf(p); return i < 0 ? BODY_PARTS.length : i; };
  return [...n].map(([part, count]) => ({ part, count })).sort((a, b) => b.count - a.count || rank(a.part) - rank(b.part) || a.part.localeCompare(b.part));
}

/** "2", "1.5": a weekly rate, one decimal at most. */
const rate = (n: number) => String(Math.round(n * 10) / 10);

/** Sessions a week so far, and how long is left to use the rest ("11 weeks", "5 days"); null once there's nothing
 *  left to plan: every session used, or the plan over. */
export function ptPace(pt: PTLike, today: string) {
  const { used: gone, left: daysLeft } = planDays(pt.starts, pt.ends, today);
  const left = Math.max(0, pt.sessions - pt.sessions_used);
  const toGo = !left || daysLeft <= 0 ? null : daysLeft >= 14 ? `${Math.round(daysLeft / 7)} weeks` : plural(daysLeft, "day");
  return { soFar: rate(pt.sessions_used / Math.max(1, gone / 7)), toGo };
}
