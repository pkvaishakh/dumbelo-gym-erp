"use client";
/* Checking a member in at the desk: search, one tap on Check In, then a sheet saying what happened. */
import { useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useMembersList } from "@/api/gen/members/members";
import type { CheckIn, Member } from "@/api/gen/model";
import { Confirm, Empty, Photo, SearchField, Sheet, Status } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { day } from "@/lib/format";
import { invalidate } from "@/lib/query";
import { useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";

type Outcome = { member: Member; checkin?: CheckIn; error?: ApiError } | null;

export function useCheckIn() {
  const qc = useQueryClient();
  const { branch, role } = useSession();
  const [outcome, setOutcome] = useState<Outcome>(null);
  const [busy, setBusy] = useState<number | null>(null);
  async function checkIn(member: Member) {
    const at = branch ?? member.home_branch ?? role.branches[0]?.id;
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

/** Search with a Check In button on each result. */
export function CheckInSearch({ autoFocus, onCancel }: { autoFocus?: boolean; onCancel?: () => void }) {
  const [q, setQ] = useState("");
  const dq = useSearch(q);
  const { branch } = useSession();
  const found = useMembersList({ q: dq, limit: 8, ...(branch ? { branch } : {}) }, { query: { enabled: dq.length >= 2 } });
  const { checkIn, outcome, busy, close } = useCheckIn();
  const rows = found.data?.data.results ?? [];
  return (
    <>
      <div className="rl-searchbar"><SearchField value={q} onChange={setQ} placeholder="Name, phone or member ID" label="Search members to check in" autoFocus={autoFocus} /></div>
      {dq.length >= 2 && (
        <section className="rl-section" aria-label="Results">
          {found.isLoading ? <p className="rl-row__meta">Searching…</p> : rows.length ? (
            <ul className="rl-card rl-results">
              {rows.map((m) => (
                <li key={m.id}><div className="rl-result">
                  <Photo name={m.name} />
                  <span className="rl-result__text"><span className="rl-row__title">{m.name}</span><span className="rl-row__meta">{m.code} • <Status status={m.status} /></span></span>
                  <button className="rl-button rl-button--sm" type="button" disabled={busy === m.id} onClick={() => checkIn(m)}>{busy === m.id ? "Checking in…" : "Check In"}</button>
                </div></li>
              ))}
            </ul>
          ) : (
            <Empty icon={Search} title={`No member matches “${dq}”`} text="Check the spelling, or add them as a new member.">
              <Link className="rl-button rl-button--block" href="/members/new">Add Member</Link>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setQ(""); onCancel?.(); }}>Clear Search</button>
            </Empty>
          )}
        </section>
      )}
      <CheckInResult outcome={outcome} onClose={() => { close(); setQ(""); }} />
    </>
  );
}
