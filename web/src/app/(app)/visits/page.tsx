"use client";
import { CalendarCheck } from "lucide-react";

import { useCheckinsListInfinite } from "@/api/gen/checkins/checkins";
import { PageBar } from "@/components/shell";
import { Empty, Icon, LoadMore, SkeletonRows } from "@/components/ui";
import { day, isoDate, plural } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

export default function VisitsPage() {
  const q = useCheckinsListInfinite(undefined, { query: paged });
  const { rows } = pages(q);
  const today = isoDate(new Date());
  // One check-in a day, latest first: the first page (50) always holds the whole of this month.
  const month = rows.filter((c) => c.local_date.slice(0, 7) === today.slice(0, 7)).length;
  return (
    <div className="rl-app rl-root">
      <PageBar title="Visits" sub={`${plural(month, "visit")} this month`} />
      <main className="rl-app__main">
        <section className="rl-section">
          {q.isLoading ? <SkeletonRows /> : rows.length ? (
            <><ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((c) => (
                <li key={c.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={CalendarCheck} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{c.local_date === today ? "Today" : day(c.local_date)}</span>
                  <span className="rl-row__meta rl-mrow__meta">{c.branch_name}{c.session ? ` • ${c.session}` : ""}</span>
                  <span className="rl-mrow__time">{c.time}</span>
                </div></li>
              ))}
            </ul>
            <LoadMore q={q} /></>
          ) : <Empty icon={CalendarCheck} title="No visits yet" text="Each time you check in, it shows up here." />}
        </section>
      </main>
    </div>
  );
}
