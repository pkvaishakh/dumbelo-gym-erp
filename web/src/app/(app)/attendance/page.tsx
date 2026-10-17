"use client";
import { CalendarX, ChevronRight, ClipboardCheck, DoorOpen, QrCode, UserCheck } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useCheckinsList, useCheckinsListInfinite } from "@/api/gen/checkins/checkins";
import type { CheckIn, Staff } from "@/api/gen/model";
import { useStaffList } from "@/api/gen/staff/staff";
import { PageBar } from "@/components/shell";
import { Chips, Empty, ErrorText, Icon, LoadMore, Photo, Section, Seg, Sheet, SkeletonRows, Stat } from "@/components/ui";
import { CheckInSearch } from "@/features/checkin";
import { isoDate, plural } from "@/lib/format";
import { paged, pages, useAction, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { CheckinSummary } from "@/lib/types";

/** How members came in, in the order the Summary shows them. */
const SOURCES = [
  { key: "device", label: "Through the turnstile", icon: DoorOpen },
  { key: "qr", label: "By wall QR", icon: QrCode },
  { key: "desk", label: "At the desk", icon: ClipboardCheck },
] as const;

function lastDays(n: number) {
  return Array.from({ length: n }, (_, i) => { const d = new Date(); d.setDate(d.getDate() - (n - 1 - i)); return d; });
}

function Attendance() {
  const params = useSearchParams();
  const { role, branch, branchName, setBranch } = useSession();
  const desk = role.role === "admin" || role.role === "receptionist";
  const isAdmin = role.role === "admin";
  const branchOptions = [
    ...(isAdmin ? [{ value: "all", label: "All branches" }] : []),
    ...role.branches.map((b) => ({ value: String(b.id), label: b.name })),
  ];
  const days = lastDays(7);
  const [date, setDate] = useState(isoDate(new Date()));
  const isToday = date === isoDate(new Date());
  const [who, setWho] = useState<"members" | "staff">(params.get("who") === "staff" ? "staff" : "members");
  const [session, setSession] = useState("all");
  const [kind, setKind] = useState<"staff" | "trainer" | "receptionist">("staff");
  const [checking, setChecking] = useState(params.get("checkin") === "1");
  const at = { date, ...(branch ? { branch } : {}) };
  // Counts come from the summary; the list below only pages through the rows.
  const summary = useGet<CheckinSummary>("/api/checkins/summary/", at);
  const list = useCheckinsListInfinite({ ...at, kind: "member", ...(session !== "all" ? { session } : {}) }, { query: paged });
  const { rows: shown, count: shownCount } = pages(list);
  const staffQ = useCheckinsList({ ...at, kind: "staff", limit: 100 }, { query: { enabled: who === "staff" } });  // a branch's staff fit one page
  const staffIn = staffQ.data?.data.results ?? [];
  const memberCount = summary.data?.totals.member ?? 0;
  const src = summary.data?.member_sources;
  const sessions = (summary.data?.sessions ?? []).filter((s) => s.member > 0);
  const label = isToday ? "Today" : new Date(date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });

  return (
    <div className="rl-app rl-root">
      <PageBar title="Attendance" sub={<>{label} â€¢ {branchName}</>} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--days">
          <div className="rl-daystrip" role="radiogroup" aria-label="Day">
            {days.map((d) => {
              const v = isoDate(d); const today = v === isoDate(new Date());
              return (
                <label className="rl-day" key={v}>
                  <input type="radio" name="at-day" value={v} checked={date === v} onChange={() => { setDate(v); setSession("all"); }} aria-label={d.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })} />
                  <span><small>{today ? "Today" : d.toLocaleDateString("en-IN", { weekday: "short" })}</small><b>{d.getDate()}</b></span>
                </label>
              );
            })}
          </div>
        </div>
        {branchOptions.length > 1 && (
          <Chips name="at-branch" label="Branch" value={branch ? String(branch) : "all"} onChange={(v) => setBranch(v === "all" ? null : Number(v))}
            style={{ marginTop: 0 }} options={branchOptions} />
        )}
        <Seg label="Whose attendance" onSurface value={who} onChange={setWho} options={[{ value: "members", label: "Members" }, { value: "staff", label: "Staff" }]} />

        {who === "members" ? (
          <>
            {desk && isToday && (
              <Section label="Check in">
                {checking ? (
                  <><CheckInSearch autoFocus onCancel={() => setChecking(false)} /><button className="rl-link rl-link--plain" type="button" onClick={() => setChecking(false)} style={{ marginTop: "var(--space-2)" }}><span>Close search</span></button></>
                ) : (
                  <button className="rl-tile rl-tile--accent rl-pressable" type="button" style={{ width: "100%" }} onClick={() => setChecking(true)}>
                    <Icon as={ClipboardCheck} /><span className="rl-tile__text">Check In Member<span className="rl-tile__hint">Search, then one tap</span></span>
                  </button>
                )}
              </Section>
            )}
            <Section label="Summary">
              <div className="rl-kpis rl-kpis--pair">
                <Stat icon={UserCheck} accent value={summary.data ? memberCount : "â€“"} label={isToday ? "Check-ins so far" : "Check-ins"}
                  note={summary.data ? (branch ? branchName : `Across ${plural(summary.data.branches?.length ?? role.branches.length, "branch", "branches")}`) : undefined} />
                {SOURCES.map((s) => (
                  <Stat key={s.key} icon={s.icon} value={src ? src[s.key] : "â€“"} label={s.label}
                    share={src && memberCount ? src[s.key] / memberCount : src ? 0 : undefined}
                    note={src ? (memberCount ? `${Math.round((src[s.key] / memberCount) * 100)}% of check-ins` : "None yet") : undefined} />
                ))}
              </div>
            </Section>
            {!branch && (summary.data?.branches?.length ?? 0) > 1 && (
              <Section title="By branch"><BranchCheckins rows={summary.data!.branches!} /></Section>
            )}
            <Section title="Check-ins">
              <Chips name="at-filter" label="Filter check-ins by session" value={session} onChange={setSession} style={{ marginTop: 0 }}
                options={[{ value: "all", label: "All", count: memberCount }, ...sessions.map((s) => ({ value: s.session, label: s.session, count: s.member }))]} />
              <div className="rl-listmeta" style={{ marginTop: "var(--space-3)" }}><p role="status">{list.isLoading ? "Loadingâ€¦" : `Showing ${plural(shown.length, "check-in")}${shown.length < shownCount ? ` of ${shownCount}` : ""}`}</p><p>Latest first</p></div>
              {list.isLoading ? <SkeletonRows /> : shown.length ? <><VisitList rows={shown} /><LoadMore q={list} /></> : (
                <Empty icon={CalendarX} title={isToday ? "No check-ins yet today" : "No check-ins this day"} text="Check-ins from the desk, the wall QR and the turnstile show up here." />
              )}
            </Section>
          </>
        ) : (
          <StaffPane checkins={staffIn} kind={kind} setKind={setKind} canCheckIn={desk && isToday} loading={staffQ.isLoading} />
        )}
      </main>
    </div>
  );
}

/** All branches: each branch's member check-ins and how they came in. Tapping one switches to that branch. */
function BranchCheckins({ rows }: { rows: NonNullable<CheckinSummary["branches"]> }) {
  const { setBranch } = useSession();
  const top = Math.max(1, ...rows.map((b) => b.member));
  return (
    <ul className="rl-card rl-brday">
      {rows.map((b) => (
        <li key={b.id}><button className="rl-brday__row" type="button" onClick={() => setBranch(b.id)}
          aria-label={`${b.name}: ${plural(b.member, "check-in")}, ${b.member_sources.device} through the turnstile, ${b.member_sources.qr} by wall QR, ${b.member_sources.desk} at the desk. Show this branch`}>
          <span className="rl-brday__top">
            <span className="rl-row__title">{b.name}</span>
            <ChevronRight className="rl-icon rl-icon--sm rl-attn__chev" strokeWidth={1.75} aria-hidden />
          </span>
          <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: b.member / top }} /></span>
          <span className="rl-brday__nums" aria-hidden="true">
            <span><b>{b.member}</b><small>Check-ins</small></span>
            <span><b>{b.member_sources.device}</b><small>Turnstile</small></span>
            <span><b>{b.member_sources.qr}</b><small>Wall QR</small></span>
            <span><b>{b.member_sources.desk}</b><small>Desk</small></span>
          </span>
        </button></li>
      ))}
    </ul>
  );
}

function VisitList({ rows }: { rows: CheckIn[] }) {
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {rows.map((c) => (
        <li key={c.id}><a className="rl-mrow" href={c.kind === "member" ? `/members/${c.person_id}` : undefined}>
          <Photo name={c.name} />
          <span className="rl-row__title rl-mrow__name">{c.name}</span>
          <span className="rl-row__meta rl-mrow__meta">{[c.code, c.session, c.source === "device" ? "Turnstile" : c.source === "qr" ? "Wall QR" : "Desk"].filter(Boolean).join(" â€¢ ")}</span>
          <span className="rl-mrow__time">{c.time}</span>
        </a></li>
      ))}
    </ul>
  );
}

function StaffPane({ checkins, kind, setKind, canCheckIn, loading }: {
  checkins: CheckIn[]; kind: "staff" | "trainer" | "receptionist"; setKind: (k: "staff" | "trainer" | "receptionist") => void; canCheckIn: boolean; loading: boolean;
}) {
  const { branch } = useSession();
  const staffQ = useStaffList({ is_active: true, limit: 100, ...(branch ? { branches: [branch] } : {}) });
  const staff = (staffQ.data?.data.results ?? []).filter((s) => s.role !== "admin");
  const byId = new Map(checkins.map((c) => [c.person_id, c]));
  const shown = staff.filter((s) => kind === "staff" || s.role === kind);
  const count = (r?: string) => { const l = staff.filter((s) => !r || s.role === r); return { in: l.filter((s) => byId.has(s.id)).length, all: l.length }; };
  const t = count("trainer"), r = count("receptionist");
  const [target, setTarget] = useState<Staff | null>(null);
  return (
    <>
      <Section label="Summary">
        <div className="rl-kpis rl-kpis--pair">
          <Stat icon={UserCheck} value={`${t.in} of ${t.all}`} label="Trainers checked in" />
          <Stat icon={UserCheck} value={`${r.in} of ${r.all}`} label="Receptionists checked in" />
        </div>
      </Section>
      <Section title="Staff">
        <Chips name="st-kind" label="Filter staff" value={kind} onChange={setKind} style={{ marginTop: 0 }} options={[
          { value: "staff", label: "Everyone", count: staff.length }, { value: "trainer", label: "Trainers", count: t.all }, { value: "receptionist", label: "Receptionists", count: r.all },
        ]} />
        {loading || staffQ.isLoading ? <SkeletonRows n={4} /> : (
          <ul className="rl-card rl-mlist rl-mlist--compact" style={{ marginTop: "var(--space-3)" }}>
            {shown.map((s) => {
              const c = byId.get(s.id);
              return (
                <li key={s.id}><div className="rl-mrow">
                  <Photo name={s.name} />
                  <span className="rl-row__title rl-mrow__name">{s.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{s.role === "trainer" ? "Trainer" : "Receptionist"}{s.shift ? ` â€¢ ${s.shift} shift` : ""}{c?.session ? ` â€¢ ${c.session}` : ""}</span>
                  {c ? <span className="rl-mrow__time">{c.time}</span> : canCheckIn ? (
                    <button className="rl-button rl-button--secondary rl-button--sm" type="button" onClick={() => setTarget(s)}>Check In</button>
                  ) : <span className="rl-status rl-status--off">Not in</span>}
                </div></li>
              );
            })}
          </ul>
        )}
      </Section>
      <StaffCheckIn staff={target} onClose={() => setTarget(null)} />
    </>
  );
}

function StaffCheckIn({ staff, onClose }: { staff: Staff | null; onClose: () => void }) {
  const { branch, role } = useSession();
  const at = branch ?? (staff?.branches[0] ?? role.branches[0]?.id);
  const a = useAction();
  async function go() {
    try { await a.run("/api/checkins/", { branch: at, staff: staff!.id }, { refresh: ["/api/checkins/", "/api/reports/"] }); onClose(); } catch { /* shown */ }
  }
  return (
    <Sheet open={!!staff} onClose={() => { a.clearError(); onClose(); }} title="Check in staff">
      {staff && <p className="rl-row__meta">Check {staff.name} in now at {role.branches.find((b) => b.id === at)?.name ?? "their branch"}.</p>}
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={go}>{a.busy ? "Checking inâ€¦" : "Check In"}</button></div>
    </Sheet>
  );
}

export default function Page() { return <Suspense><Attendance /></Suspense>; }
