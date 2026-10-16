"use client";
import Link from "next/link";

import type { Member } from "@/api/gen/model";
import { Photo, Status } from "@/components/ui";
import { dayShort, rupees } from "@/lib/format";
import type { TrainerMember } from "@/lib/types";

type Row = Pick<Member, "id" | "code" | "name"> & { status: string; plan?: Member["plan"] | null; plan_ends?: string | null; balance_paise?: number; payment_due?: boolean };

/** One member in a list: name and status on the first line, ID and plan on the second, the date that matters on the right. */
export function MemberRow({ m }: { m: Row | Member | TrainerMember }) {
  const r = m as Row;
  const ends = r.plan?.ends ?? r.plan_ends ?? null;
  const note =
    r.status === "due" && r.balance_paise ? { text: `${rupees(r.balance_paise)} due`, warn: true }
    : r.status === "due" ? { text: "Payment due", warn: true }
    : r.status === "expired" && ends ? { text: `Ended ${dayShort(ends)}` }
    : r.status === "none" ? { text: "No plan" }
    : ends ? { text: `Ends ${dayShort(ends)}` } : null;
  return (
    <li>
      <Link className="rl-mrow" href={`/members/${m.id}`}>
        <Photo name={m.name} />
        <span className="rl-row__title rl-mrow__name">{m.name}</span>
        <span className="rl-row__meta rl-mrow__meta">{m.code}{r.plan?.name && <span className="rl-mrow__inline"> • {r.plan.name}</span>}</span>
        <span className="rl-mrow__cell rl-mrow__cell--plan">{r.plan?.name ?? "—"}</span>
        <span className="rl-mrow__cell rl-mrow__cell--visit">{ends ? dayShort(ends) : "—"}</span>
        <Status status={r.status} />
        {note && <span className={`rl-mrow__note${note.warn ? " rl-mrow__note--warn" : ""}`}>{note.text}</span>}
      </Link>
    </li>
  );
}
