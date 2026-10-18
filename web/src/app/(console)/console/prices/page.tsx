"use client";
import { AlertCircle, BadgeIndianRupee, Building2, Cpu, MessageCircle, Receipt, StickyNote, Store } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { PriceList } from "@/api/gen/model";
import { usePlatformPricesListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { AddButton, Details, Empty, Icon, LoadMore, Section, Sheet, SkeletonRows } from "@/components/ui";
import { day, gymToday, plural, rupees } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

const RACKLINE_TZ = "Asia/Kolkata"; // price lists start on Rackline's own day

function when(p: PriceList, today: string) {
  if (p.is_current) return { label: "Current", badge: "active" };
  return p.active_from > today ? { label: "Upcoming", badge: "frozen" } : { label: "Earlier", badge: "off" };
}

/** Rackline's price lists, newest first. A list is never edited: new prices are a new list, and each gym moves to
 *  them from its Rackline plan. */
export default function PricesPage() {
  const list = usePlatformPricesListInfinite(undefined, { query: paged });
  const { rows } = pages(list);
  const today = gymToday(RACKLINE_TZ);
  const [open, setOpen] = useState<PriceList | null>(null);
  const current = rows.find((p) => p.is_current);
  return (
    <div className="rl-app rl-root">
      <PageBar title="Prices" back="/console/more" sub={current ? `Current since ${day(current.active_from)}` : "What gyms pay Rackline"} action={<AddButton href="/console/prices/new" label="Add Price List" />} />
      <main className="rl-app__main">
        <Section label="Price lists">
          {list.isLoading ? <SkeletonRows n={3} /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the prices" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((p) => {
                  const s = when(p, today);
                  return (
                    <li key={p.id}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => setOpen(p)}>
                      <span className="rl-chipicon" aria-hidden="true"><Icon as={BadgeIndianRupee} size="sm" /></span>
                      <span className="rl-row__title rl-mrow__name">From {day(p.active_from)}</span>
                      <span className="rl-row__meta rl-mrow__meta">{rupees(p.base_paise)} + {rupees(p.per_branch_paise)} a branch • {plural(p.gym_count, "gym")}</span>
                      <span className={`rl-status rl-status--${s.badge}`}>{s.label}</span>
                    </button></li>
                  );
                })}
              </ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={BadgeIndianRupee} title="No prices yet" text="Add Rackline's prices before opening the first gym: every gym's plan starts from them.">
              <Link className="rl-button rl-button--block" href="/console/prices/new">Add Price List</Link>
            </Empty>
          )}
        </Section>
        <p className="rl-row__meta">A new price list never changes what a gym pays by itself. Open the gym and use Move to Current Prices on its Rackline plan.</p>
      </main>
      <Sheet open={!!open} onClose={() => setOpen(null)} title={open ? `Prices from ${day(open.active_from)}` : undefined}>
        {open && (
          <Details rows={[
            { icon: Receipt, label: "Base fee", value: `${rupees(open.base_paise)} a month` },
            { icon: Store, label: "Per branch", value: `${rupees(open.per_branch_paise)} a month` },
            { icon: MessageCircle, label: "WhatsApp setup", value: `${rupees(open.whatsapp_setup_paise)} once` },
            { icon: Cpu, label: "Attendance machine setup", value: `${rupees(open.machine_setup_paise)} once, for each machine` },
            { icon: MessageCircle, label: "Each delivered message on Rackline's number", value: `${rupees(open.utility_message_paise)} reminders and receipts • ${rupees(open.marketing_message_paise)} offers • ${rupees(open.authentication_message_paise)} sign-in codes` },
            { icon: Building2, label: "Gyms on these prices", value: plural(open.gym_count, "gym") },
            ...(open.note ? [{ icon: StickyNote, label: "Note", value: open.note }] : []),
          ]} />
        )}
      </Sheet>
    </div>
  );
}
