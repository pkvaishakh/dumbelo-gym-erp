"use client";
import { AlertCircle, Building2, IndianRupee, MessageCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { usePlatformWhatsappUsageRetrieveInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { Empty, Field, Icon, LoadMore, Section, SkeletonRows, Stat } from "@/components/ui";
import { logUrl, NO_FILTERS } from "@/features/console/message-log";
import { gymToday, monthLabel, plural, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";
import { recentMonths } from "@/lib/messages";

/** Console → WhatsApp usage: each gym's messages delivered from Rackline's shared number in a month, and what they
 *  came to, the biggest first. Each gym's days are its own, as its invoice counts them. A gym opens its log, showing
 *  just the messages counted here. */
function Usage() {
  const params = useSearchParams();
  const router = useRouter();
  const thisMonth = gymToday("Asia/Kolkata").slice(0, 7); // Rackline's month, as on Console Home
  const asked = params.get("month") ?? "";
  const month = /^\d{4}-(0[1-9]|1[0-2])$/.test(asked) ? asked : thisMonth;
  const list = usePlatformWhatsappUsageRetrieveInfinite({ month }, { query: paged });
  const { rows, count } = pages(list);
  const totals = list.data?.pages[0]?.data;

  return (
    <div className="rl-app rl-root">
      <PageBar title="WhatsApp usage" sub={`Rackline's shared number • ${monthLabel(month)}`} back="/console/more" />
      <main className="rl-app__main">
        <Field label="Month">{(id) => (
          <select className="rl-field__input" id={id} value={month} onChange={(e) => router.replace(`/console/usage?month=${e.target.value}`, { scroll: false })}>
            {[...new Set([...recentMonths(thisMonth), month])].map((m) => <option key={m} value={m}>{monthLabel(m)}</option>)}
          </select>
        )}</Field>
        <Section label="Totals">
          <div className="rl-kpis rl-kpis--pair">
            <Stat icon={IndianRupee} accent value={totals ? rupees(totals.amount_paise) : "–"} label={month === thisMonth ? "Billed so far" : "Billed"}
              note={totals ? `Across ${plural(count, "gym")}` : undefined} />
            <Stat icon={MessageCircle} value={totals ? totals.messages.toLocaleString("en-IN") : "–"} label="Messages delivered" />
          </div>
        </Section>
        <Section title="By gym">
          {list.isLoading ? <SkeletonRows /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the usage" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((g) => (
                  <li key={g.gym}><Link className="rl-mrow" href={logUrl({ ...NO_FILTERS, gym: String(g.gym), billed: month })}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={Building2} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{g.gym_name}</span>
                    <span className="rl-row__meta rl-mrow__meta">{plural(g.messages, "message")} delivered</span>
                    <span className="rl-mrow__note">{rupees(g.amount_paise)}</span>
                  </Link></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={MessageCircle} title={`No messages in ${monthLabel(month)}`} text="Gyms on Rackline's number show up here once their messages are delivered." />
          )}
        </Section>
        <p className="rl-row__meta">A gym&apos;s messages go on the invoice written on its billing day, for the billing month before. Gyms on their own number pay Meta and aren&apos;t here.</p>
      </main>
    </div>
  );
}

export default function Page() { return <Suspense><Usage /></Suspense>; }
