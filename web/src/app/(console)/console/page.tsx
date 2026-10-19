"use client";
import { AlarmClock, AlertCircle, Building2, ChevronRight, CircleCheck, CirclePause, Hourglass, IndianRupee, MessageCircle, RotateCw, Send } from "lucide-react";
import Link from "next/link";

import type { PlatformSummary } from "@/api/gen/model";
import { usePlatformSummaryRetrieve } from "@/api/gen/platform/platform";
import { HomeBar } from "@/components/shell";
import { Details, Empty, Icon, Section, SkeletonRows } from "@/components/ui";
import { CHECK_ICON, RunBadge, StateBadge } from "@/features/console/server";
import { Attention, GlanceLoading } from "@/features/homes";
import { consoleAttention } from "@/lib/console-home";
import { ago, greeting, plural, rupees } from "@/lib/format";
import { useWho } from "@/lib/session";

const count = (n: number) => n.toLocaleString("en-IN");

/** Console → Home, where a Dumbelo admin lands: the gyms, what they owe Dumbelo, what needs you, today's WhatsApp
 *  messages and the server, from one summary. Counts and Dumbelo's own money only, never inside a gym. */
export default function ConsoleHome() {
  const { me } = useWho();
  const q = usePlatformSummaryRetrieve({ query: { refetchInterval: 60_000 } });
  const s = q.data?.data;
  const sub = s ? (s.gyms.new_this_month ? `${plural(s.gyms.new_this_month, "new gym")} this month` : "No new gyms this month") : "Dumbelo Console";
  return (
    <div className="rl-app rl-root">
      <HomeBar home="/console" />
      <main className="rl-app__main">
        <div className="rl-greeting">
          <h1 className="rl-greeting__hello">{greeting(me.name, true)}</h1>
          <p className="rl-appbar__branch" style={{ margin: 0 }}>{sub}</p>
        </div>
        {q.isError ? (
          <Empty icon={AlertCircle} title="Can't load Home" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
          </Empty>
        ) : (
          <>
            <Section label="Dumbelo at a glance">
              <div aria-busy={!s}>{s ? <Glance s={s} /> : <GlanceLoading />}</div>
            </Section>
            <div className="rl-app__cols">
              <div className="rl-app__col">
                <Section title="Needs attention">
                  {s ? <Attention rows={consoleAttention(s)} /> : <SkeletonRows n={2} />}
                </Section>
                <Section title="WhatsApp today" aside={<Link className="rl-link" href="/console/messages"><span>Open Log</span></Link>}>
                  {s ? (
                    <Details rows={[
                      { icon: Send, label: "Delivered", value: count(s.whatsapp.delivered_today) },
                      { icon: AlertCircle, label: "Failed", value: count(s.whatsapp.failed_today) },
                      { icon: RotateCw, label: "Waiting for a retry", value: count(s.whatsapp.waiting_retry) },
                    ]} />
                  ) : <SkeletonRows n={3} />}
                </Section>
              </div>
              <div className="rl-app__col">
                <Section title="Server" aside={<Link className="rl-link" href="/console/server"><span>Open Server</span></Link>}>
                  {s ? <ServerCard s={s} /> : <SkeletonRows n={2} />}
                </Section>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

/** What gyms owe Dumbelo on the ink card (overdue and the shared number's month beside it), then the gyms by status.
 *  Each figure opens the gyms or messages it counts. */
function Glance({ s }: { s: PlatformSummary }) {
  const m = s.money;
  const people = [
    { n: s.gyms.active, label: "Active", note: "Billed monthly", icon: Building2, href: "/console/gyms?status=active" },
    { n: s.gyms.trial, label: "On trial", note: "Not billed yet", icon: Hourglass, href: "/console/gyms?status=trial" },
    { n: s.gyms.suspended, label: "Suspended", note: "App paused", icon: CirclePause, href: "/console/gyms?status=suspended" },
  ];
  return (
    <div className="rl-glance">
      <div className="rl-glance__money">
        <Link className="rl-glance__hero rl-pressable" href="/console/gyms?owes=any">
          <span className="rl-glance__head">
            <span className="rl-glance__chip" aria-hidden="true"><Icon as={IndianRupee} size="sm" /></span>
            <span className="rl-glance__kicker">Owed to Dumbelo</span>
            <ChevronRight className="rl-icon rl-icon--sm rl-glance__chev" strokeWidth={1.75} aria-hidden />
          </span>
          <span className="rl-glance__big">{rupees(m.owed_paise)}</span>
          <span className="rl-glance__note">{m.gyms_owing ? `From ${plural(m.gyms_owing, "gym")}` : "Every invoice is paid"}</span>
        </Link>
        <div className="rl-glance__pair">
          <Link className="rl-glance__cell rl-pressable" href="/console/gyms?owes=overdue">
            <span className="rl-glance__label"><Icon as={AlarmClock} size="sm" />Overdue</span>
            <span className="rl-glance__value">{rupees(m.overdue_paise)}</span>
            <span className="rl-glance__note">{m.overdue_invoices ? plural(m.overdue_invoices, "invoice") : "Nothing late"}</span>
          </Link>
          <Link className="rl-glance__cell rl-pressable" href="/console/messages">
            <span className="rl-glance__label"><Icon as={MessageCircle} size="sm" />Shared number</span>
            <span className="rl-glance__value">{rupees(s.whatsapp.shared_paise)}</span>
            <span className="rl-glance__note">{plural(s.whatsapp.shared_messages, "message")} this month</span>
          </Link>
        </div>
      </div>
      <div className="rl-glance__people">
        {people.map((p) => (
          <Link className="rl-glance__cell rl-pressable" href={p.href} key={p.label}>
            <span className="rl-glance__label"><Icon as={p.icon} size="sm" />{p.label}</span>
            <span className="rl-glance__value">{count(p.n)}</span>
            <span className="rl-glance__note">{p.note}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

/** The checks that are down and the jobs whose last run failed, each opening Server; one calm row when all is well. */
function ServerCard({ s }: { s: PlatformSummary }) {
  const { down, failed_jobs: failed } = s.server;
  if (!down.length && !failed.length) {
    return (
      <ul className="rl-card rl-mlist rl-mlist--compact">
        <li><Link className="rl-mrow" href="/console/server">
          <span className="rl-chipicon" aria-hidden="true"><Icon as={CircleCheck} size="sm" /></span>
          <span className="rl-row__title rl-mrow__name">Everything is answering</span>
          <span className="rl-row__meta rl-mrow__meta">No job&apos;s last run failed</span>
          <StateBadge state="up" />
        </Link></li>
      </ul>
    );
  }
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact">
      {down.map((c) => (
        <li key={c.key}><Link className="rl-mrow" href="/console/server">
          <span className="rl-chipicon" aria-hidden="true"><Icon as={CHECK_ICON[c.key] ?? AlertCircle} size="sm" /></span>
          <span className="rl-row__title rl-mrow__name">{c.label}</span>
          <span className="rl-row__meta rl-mrow__meta">{c.at ? `Last ticked ${ago(c.at)}` : c.detail}</span>
          <StateBadge state={c.state} />
        </Link></li>
      ))}
      {failed.map((j) => (
        <li key={j.job}><Link className="rl-mrow" href="/console/server">
          <span className="rl-chipicon" aria-hidden="true"><Icon as={AlertCircle} size="sm" /></span>
          <span className="rl-row__title rl-mrow__name">{j.label}</span>
          <span className="rl-row__meta rl-mrow__meta">Last run failed {ago(j.finished_at)}</span>
          <RunBadge state="failed" />
        </Link></li>
      ))}
    </ul>
  );
}
