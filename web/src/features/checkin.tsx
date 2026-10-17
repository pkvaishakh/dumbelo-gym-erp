"use client";
/* Checking a member in at the desk: search, one tap on Check In, then a sheet saying what happened. */
import { useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useMembersList } from "@/api/gen/members/members";
import type { CheckIn, Member } from "@/api/gen/model";
import { Confirm, Empty, Photo, SearchField, Sheet, Status } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { day } from "@/lib/format";
import { invalidate } from "@/lib/query";
import { useSession } from "@/lib/session";

type Outcome = { member: Member; checkin?: CheckIn; error?: ApiError } | null;

export function useCheckIn() {
  const qc = useQueryClient();
  const { branch, role } = useSession();
  const [outcome, setOutcome] = useState<Outcome>(null);
  const [busy, setBusy] = useState<number | null>(null);
  async function checkIn(member: Member) {
    const home = role.branches.some((b) => b.id === member.home_branch) ? member.home_branch : undefined;
    const at = branch ?? home ?? role.branches[0]?.id;
    setBusy(member.id);
    try {
      const c = await api<CheckIn>("/api/checkins/", { method: "POST", json: { branch: at, member: member.id } });
      setOutcome({ member, checkin: c });
      await invalidate(qc, "/api/checkins/", "/api/reports/");
    } catch (e) {
      setOutcome({ member, error: e instanceof ApiError ? e : new ApiError(0, "network", "Can't reach Rackline. Try again.") });
    } finally {
      setBusy(null);
    }
  }
  return { checkIn, outcome, busy, close: () => setOutcome(null) };
}

export function CheckInResult({ outcome, onClose }: { outcome: Outcome; onClose: () => void }) {
  const m = outcome?.member;
  const blocked = !!outcome?.error;
  const code = outcome?.error?.code;
  const title = !outcome ? "" : !blocked ? `${m!.name} is checked in` : code === "already_checked_in" ? "Already checked in" : "Check-in blocked";
  return (
    <Sheet open={!!outcome} onClose={onClose}>
      {m && (
        <>
          <Confirm blocked={blocked && code !== "already_checked_in"} title={title} text={blocked ? outcome!.error!.message : `At ${outcome!.checkin!.time}, ${outcome!.checkin!.branch_name}`} />
          <div className="rl-idcard">
            <div className="rl-idcard__who">
              <Photo name={m.name} size="lg" />
              <span><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code}</span><Status status={m.status} /></span>
            </div>
            {m.plan && (
              <dl className="rl-facts"><dt>Plan</dt><dd>{m.plan.name}</dd><dt>{m.status === "expired" ? "Expired on" : "Valid until"}</dt><dd>{day(String(m.plan.ends))}</dd></dl>
            )}
          </div>
          <div className="rl-sheet__actions">
            {blocked && (code === "membership_expired") && <Link className="rl-button rl-button--block" href={`/subscriptions/new?member=${m.id}`}>Renew Membership</Link>}
            {m.status === "due" && !blocked && <Link className="rl-button rl-button--secondary rl-button--block" href={`/payments/new?member=${m.id}`}>Collect Payment</Link>}
            <button className={`rl-button rl-button--block${blocked && code === "membership_expired" ? " rl-button--secondary" : ""}`} type="button" onClick={onClose}>Done</button>
          </div>
        </>
      )}
    </Sheet>
  );
}

/** Search with a Check In button on each result. It searches when the desk presses Enter (Search on a phone's
 *  keyboard), not on every keystroke: one request per member looked up, and the list doesn't shift while typing. */
export function CheckInSearch({ hint }: { hint?: boolean }) {
  const [q, setQ] = useState("");
  const [dq, setDq] = useState("");  // what was last searched for
  const [short, setShort] = useState(false);
  const box = useRef<HTMLFormElement>(null);
  const { branch } = useSession();
  const type = (v: string) => { setQ(v); setShort(false); if (!v.trim()) setDq(""); };
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const term = q.trim();
    if (term.length < 2) { setShort(!!term); setDq(""); return; }
    setDq(term);
    (document.activeElement as HTMLElement | null)?.blur();  // put the phone keyboard away so the results show
  };
  const found = useMembersList({ q: dq, limit: 8, ...(branch ? { branch } : {}) }, { query: { enabled: dq.length >= 2 } });
  const { checkIn, outcome, busy, close } = useCheckIn();
  const rows = found.data?.data.results ?? [];
  return (
    <>
      <form className="rl-searchbar" ref={box} role="search" onSubmit={submit}>
        <SearchField value={q} onChange={type} placeholder="Name, phone or member ID" label="Search members to check in" />
      </form>
      {short ? <p className="rl-row__meta rl-checkin__hint" role="status">Type at least 2 letters or digits, then search.</p>
        : hint && !dq && <p className="rl-row__meta rl-checkin__hint">Type a name, phone number or member ID, then press Search on your keyboard.</p>}
      {dq.length >= 2 && (
        <section className="rl-section" aria-label="Results">
          {found.isLoading ? <p className="rl-row__meta">Searching…</p> : rows.length ? (
            <ul className="rl-card rl-results">
              {rows.map((m) => (
                <li key={m.id}><div className="rl-result">
                  <Photo name={m.name} />
                  <span className="rl-result__text"><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code} • <Status status={m.status} /></span></span>
                  <button className="rl-button rl-button--accent rl-button--sm" type="button" disabled={busy === m.id} onClick={() => checkIn(m)}>{busy === m.id ? "Checking in…" : "Check In"}</button>
                </div></li>
              ))}
            </ul>
          ) : (
            <Empty icon={Search} title={`No member matches “${dq}”`} text="Check the spelling, or add them as a new member.">
              <Link className="rl-button rl-button--block" href="/members/new">Add Member</Link>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => type("")}>Clear Search</button>
            </Empty>
          )}
        </section>
      )}
      {/* After Done, the search is empty and focused again: ready for the next member in the queue. */}
      <CheckInResult outcome={outcome} onClose={() => { close(); type(""); requestAnimationFrame(() => box.current?.querySelector("input")?.focus()); }} />
    </>
  );
}

/** Check In Member as a bottom sheet: it slides up over Home with the search focused, and stays open so the desk
 *  can check in one member after another. */
export function CheckInSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const box = useRef<HTMLDivElement>(null);
  // The sheet focuses itself as it opens; this runs after that, so the keyboard comes up on the search.
  useEffect(() => { if (open) box.current?.querySelector("input")?.focus(); }, [open]);
  return (
    <Sheet open={open} onClose={onClose} title="Check In Member">
      <div className="rl-checkin-sheet" ref={box}><CheckInSearch hint /></div>
    </Sheet>
  );
}
