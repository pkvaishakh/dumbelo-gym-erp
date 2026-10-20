/* The landing page's phones: each role's home drawn with the design system's own markup, at the app's 390px width,
 * then scaled down by the frame. Pictures only: aria-hidden and inert, nothing in them can be focused or tapped.
 * Rendered on the server: none of this markup is sent to the browser as script. */
import {
  AlertTriangle, BarChart3, Bell, CalendarCheck, ChevronRight, Home, IndianRupee, LayoutGrid, ListChecks, Plus, QrCode,
  ScanLine, Search, TrendingUp, UserPlus, Users, type LucideIcon,
} from "lucide-react";

import { Icon, Mark } from "@/components/brand";

import s from "./landing.module.css";

export type Role = "admin" | "desk" | "trainer" | "member";

/** A phone with real thickness: the face, then edge layers stepped back in depth so its side shows when it turns. */
export function Phone({ role, className = "" }: { role: Role; className?: string }) {
  return (
    <div className={`${s.phone} ${className}`} aria-hidden="true" inert>
      <span className={s.phoneEdge} style={{ "--z": 1 } as React.CSSProperties} />
      <span className={s.phoneEdge} style={{ "--z": 2 } as React.CSSProperties} />
      <span className={s.phoneEdge} style={{ "--z": 3 } as React.CSSProperties} />
      <span className={s.phoneEdge} style={{ "--z": 4 } as React.CSSProperties} />
      <div className={s.phoneFace}>
        <div className={s.screen}>
          <div className={`${s.screenIn} rl-root`}>{SCREENS[role]()}</div>
        </div>
      </div>
    </div>
  );
}

function AppBar({ hello, branch, initials, unread }: { hello: string; branch: string; initials: string; unread?: number }) {
  return (
    <header className={`rl-appbar ${s.mockBar}`}>
      <div className="rl-appbar__in">
        <span className="rl-logo"><Mark /></span>
        <div className="rl-appbar__who"><p className="rl-appbar__hello">{hello}</p><p className="rl-appbar__branch">{branch}</p></div>
        <span className="rl-iconbtn"><Icon as={Bell} />{unread ? <span className="rl-badge">{unread}</span> : null}</span>
        <span className="rl-avatar">{initials}</span>
      </div>
    </header>
  );
}

function Tabs({ tabs, fab }: { tabs: [LucideIcon, string][]; fab?: boolean }) {
  const cells = tabs.map(([I, label], i) => (
    <span key={label} className="rl-tab" aria-current={i === 0 ? "page" : undefined}><span className="rl-tab__icon"><Icon as={I} /></span>{label}</span>
  ));
  if (fab) cells.splice(2, 0, <span key="fab" className="rl-fab"><Icon as={Plus} /></span>);
  return <nav className={`rl-tabbar ${s.mockTabs}`}><div className="rl-tabbar__in">{cells}</div></nav>;
}

function Stat({ icon, value, label, note }: { icon: LucideIcon; value: string; label: string; note?: React.ReactNode }) {
  return (
    <div className="rl-stat">
      <span className="rl-stat__icon"><Icon as={icon} size="sm" /></span>
      <p className="rl-stat__value">{value}</p>
      <p className="rl-stat__label">{label}</p>
      {note}
    </div>
  );
}

function Row({ name, meta, status, label, icon, time }: {
  name: string; meta: string; status?: string; label?: string; icon?: LucideIcon; time?: string;
}) {
  return (
    <div className={s.mockRow}>
      {icon ? <span className="rl-chipicon"><Icon as={icon} size="sm" /></span> : <span className="rl-photo">{name.split(" ").map((w) => w[0]).join("")}</span>}
      <span className={s.mockRowText}><span className="rl-row__title">{name}</span><span className="rl-row__meta">{meta}</span></span>
      {status && <span className={`rl-status rl-status--${status}`}>{label}</span>}
      {time && <span className={s.mockTime}>{time}</span>}
    </div>
  );
}

function Attention({ rows }: { rows: [string, string, string][] }) {
  return (
    <ul className="rl-attn">
      {rows.map(([count, title, meta]) => (
        <li key={title}>
          <span className="rl-attn__row">
            <span className="rl-attn__count">{count}</span>
            <span className="rl-attn__text"><span className="rl-row__title">{title}</span><span className="rl-row__meta">{meta}</span></span>
            <Icon as={ChevronRight} size="sm" />
          </span>
        </li>
      ))}
    </ul>
  );
}

const WEEK = [0.42, 0.58, 0.5, 0.72, 0.64, 0.86, 0.94];

const SCREENS: Record<Role, () => React.ReactNode> = {
  admin: () => (
    <>
      <AppBar hello="Good evening, Meera" branch="All branches" initials="MN" unread={5} />
      <main className={s.mockMain}>
        <div className={s.mockPair}>
          <Stat icon={IndianRupee} value="₹48,650" label="Today’s collection"
            note={<p className="rl-trend"><Icon as={TrendingUp} size="xs" /><span>+12% vs yesterday</span></p>} />
          <Stat icon={CalendarCheck} value="64" label="Check-ins today" note={<p className="rl-stat__note">12 since 8 AM</p>} />
        </div>
        <div className={s.mockTriple}>
          <span className="rl-tile rl-tile--stack"><Icon as={UserPlus} /><span>Add Member</span></span>
          <span className="rl-tile rl-tile--stack"><Icon as={IndianRupee} /><span>Collect Payment</span></span>
          <span className="rl-tile rl-tile--stack"><Icon as={ListChecks} /><span>Assign Task</span></span>
        </div>
        <section>
          <h2 className={`rl-section__title ${s.mockTitle}`}>Needs attention</h2>
          <Attention rows={[["23", "Memberships expiring soon", "In the next 7 days"], ["14", "Pending payments", "₹62,300 due"]]} />
        </section>
        <section className="rl-card rl-card--pad">
          <p className="rl-stat__label">Collection, last 7 days</p>
          <p className="rl-stat__value">₹3,05,340</p>
          <div className={s.mockChart}>
            {WEEK.map((v, i) => <span key={i} className={i === WEEK.length - 1 ? s.mockBarNow : undefined} style={{ "--v": v } as React.CSSProperties} />)}
          </div>
        </section>
      </main>
      <Tabs fab tabs={[[Home, "Home"], [CalendarCheck, "Attendance"], [BarChart3, "Reports"], [LayoutGrid, "More"]]} />
    </>
  ),
  desk: () => (
    <>
      <AppBar hello="Good morning, Alex 👋" branch="Indiranagar branch" initials="AD" unread={3} />
      <main className={s.mockMain}>
        <div className="rl-searchfield">
          <span className="rl-searchfield__open"><Icon as={Search} size="sm" /><span>Search name, phone or member ID</span></span>
          <span className="rl-searchfield__btn"><Icon as={ScanLine} /></span>
        </div>
        <span className="rl-tile rl-tile--accent">
          <Icon as={CalendarCheck} />
          <span className="rl-tile__text">Check In Member<span className="rl-tile__hint">Search or scan, then one tap</span></span>
          <Icon as={ChevronRight} size="sm" />
        </span>
        <div className={s.mockPair}>
          <Stat icon={CalendarCheck} value="64" label="Check-ins today" />
          <Stat icon={Users} value="3" label="Expiring today" note={<p className="rl-stat__note"><span className="rl-status rl-status--expiring">Expiring</span></p>} />
        </div>
        <section className="rl-card">
          <Row name="Rahul Kumar" meta="Checked in 6:42 AM" status="active" label="Active" />
          <Row name="Karthik Iyer" meta="Checked in 6:51 AM" status="expiring" label="Expiring" />
          <Row name="Farhan Ali" meta="Checked in 7:05 AM" status="due" label="Payment due" />
          <Row name="Priya Shah" meta="Checked in 7:12 AM" status="active" label="Active" />
        </section>
      </main>
      <Tabs fab tabs={[[Home, "Home"], [Users, "Members"], [CalendarCheck, "Attendance"], [LayoutGrid, "More"]]} />
    </>
  ),
  trainer: () => (
    <>
      <AppBar hello="Good morning, Arjun 👋" branch="Indiranagar branch" initials="AR" unread={2} />
      <main className={s.mockMain}>
        <div className={s.mockPair}>
          <Stat icon={Users} value="18" label="My members" />
          <Stat icon={AlertTriangle} value="4" label="Need attention" />
        </div>
        <section>
          <h2 className={`rl-section__title ${s.mockTitle}`}>My tasks</h2>
          <div className="rl-card">
            <Row icon={ListChecks} name="Plan Sneha's new routine" meta="Due today" status="tk-doing" label="In progress" />
            <Row icon={ListChecks} name="Clean the cable machine" meta="Due 22 Oct" status="tk-todo" label="To do" />
          </div>
        </section>
        <section>
          <h2 className={`rl-section__title ${s.mockTitle}`}>Members to follow up</h2>
          <div className="rl-card">
            <Row name="Sneha Rao" meta="98450 21177" status="due" label="Payment due" />
            <Row name="Karthik Iyer" meta="98860 40912" status="expiring" label="Expiring" />
            <Row name="Vikram Das" meta="99001 63528" status="frozen" label="Frozen" />
          </div>
        </section>
      </main>
      <Tabs tabs={[[Home, "Home"], [Users, "My Members"], [ListChecks, "My Tasks"], [LayoutGrid, "More"]]} />
    </>
  ),
  member: () => (
    <>
      <AppBar hello="Good morning, Rahul 👋" branch="Indiranagar branch" initials="RK" />
      <main className={s.mockMain}>
        <div className="rl-pass">
          <span className="rl-pass__top"><span className="rl-status rl-status--active">Active</span><span className="rl-pass__plan">Premium Plan</span></span>
          <p className="rl-figure">24 <small>days remaining</small></p>
          <span className="rl-bar"><span className="rl-bar__fill" style={{ "--v": 0.736 } as React.CSSProperties} /></span>
          <span className="rl-pass__dates"><span>29 Jul 2026</span><span>Expires 28 Oct 2026</span></span>
        </div>
        <span className="rl-button rl-button--accent rl-button--block"><Icon as={QrCode} />Check In</span>
        <section className="rl-card rl-card--pad rl-streak">
          <p className="rl-figure">8 🔥 <small>days in a row</small></p>
          <p className="rl-row__meta">You&apos;ve checked in 8 days in a row. Check in today to make it 9.</p>
        </section>
        <section>
          <h2 className={`rl-section__title ${s.mockTitle}`}>Recent visits</h2>
          <div className="rl-card">
            <Row icon={CalendarCheck} name="Yesterday" meta="Indiranagar • Morning" time="6:38 AM" />
            <Row icon={CalendarCheck} name="18 Oct" meta="Indiranagar • Morning" time="6:45 AM" />
            <Row icon={CalendarCheck} name="17 Oct" meta="Indiranagar • Evening" time="7:02 PM" />
          </div>
        </section>
      </main>
      <Tabs tabs={[[Home, "Home"], [QrCode, "Check In"], [CalendarCheck, "Visits"], [LayoutGrid, "More"]]} />
    </>
  ),
};
