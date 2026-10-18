"use client";
/* Pieces every report screen uses: the headline card, trends, the one-series chart and bar lists (see Reports.md). */
import { format, parseISO } from "date-fns";
import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import dynamic from "next/dynamic";

import type { ChartPoint } from "@/components/chart";
import { Icon, Section } from "@/components/ui";
import { rupees, rupeesShort, trend } from "@/lib/format";

// Charts are the heaviest part of a report and sit below its headline: load them after the screen.
const Chart = dynamic(() => import("@/components/chart").then((m) => m.Chart), {
  ssr: false,
  loading: () => <div className="rl-skel" style={{ height: "var(--chart-height)", marginTop: "var(--space-4)" }} aria-hidden="true" />,
});

type Change = { dir: "up" | "down" | "flat"; text: string };

/** An arrow and the change in words. Text in ink: the arrow carries the direction, not a colour. */
export function TrendText({ t }: { t: Change }) {
  return <><Icon as={t.dir === "up" ? TrendingUp : t.dir === "down" ? TrendingDown : Minus} size="xs" /><span>{t.text}</span></>;
}

/** "+9% vs previous 7 days" */
export function Trend({ now, before, days }: { now: number; before: number; days: number }) {
  return <TrendText t={trend(now, before, days)} />;
}

/** Money that can be below zero (a plan refunded more than it took in these days): "−₹500". */
export const signedRupees = (p: number) => `${p < 0 ? "−" : ""}${rupees(Math.abs(p))}`;

/** The headline of a report: the figure in `metric`, what it is, its change, then the chart and anything else. */
export function Lead({ title, value, label, change, aside, children }: {
  title: string; value: string; label: string; change?: Change; aside?: React.ReactNode; children?: React.ReactNode;
}) {
  return (
    <Section title={title} aside={aside}>
      <div className="rl-card rl-card--pad rl-report">
        <p className="rl-report__value">{value}</p>
        <p className="rl-perf__label">{label}</p>
        {change && <p className="rl-trend"><TrendText t={change} /></p>}
        {children}
      </div>
    </Section>
  );
}

type Dated = { date: string };

/** One point a day up to a month, then one a week: daily figures over months are mostly noise. Weeks end on the last
 *  day, so a short week falls at the start rather than looking like a drop at the end. */
export function points<T extends Dated>(series: T[], value: (d: T) => number, text: (n: number) => string, today: string): ChartPoint[] {
  if (series.length > 31) {
    const weeks: ChartPoint[] = [];
    for (let end = series.length; end > 0; end -= 7) {
      const chunk = series.slice(Math.max(0, end - 7), end);
      const total = chunk.reduce((sum, d) => sum + value(d), 0);
      const start = parseISO(chunk[0]!.date);
      weeks.unshift({ tick: format(start, "d MMM"), label: `Week of ${format(start, "d MMM")}`, value: Math.max(0, total), text: text(total) });
    }
    return weeks;
  }
  return series.map((d) => {
    const at = parseISO(d.date);
    const tick = series.length <= 7 ? (d.date === today ? "Today" : format(at, "EEE")) : format(at, "d MMM");
    // A day refunds outweigh can net below zero: the bar stays at zero, the words keep the sign.
    return { tick, label: format(at, "EEE d MMM"), value: Math.max(0, value(d)), text: text(value(d)) };
  });
}

/** A report's series as the design's chart: bars for a week, a line for longer, the last day in volt when it's today. */
export function SeriesChart<T extends Dated>({ series, label, value, text, money, today }: {
  series: T[]; label: string; value: (d: T) => number; text: (n: number) => string; money?: boolean; today: string;
}) {
  const short = money ? rupeesShort : String;
  return <Chart points={points(series, value, text, today)} label={label} axis={short} cap={short} latest={series.at(-1)?.date === today} line={series.length > 14} />;
}

export type Bar = { key: string; label: string; value: number; text: string };

/** Compare parts: one ink bar per row, scaled to the largest, the value in words beside the name. */
export function BarList({ rows }: { rows: Bar[] }) {
  const max = Math.max(1, ...rows.map((x) => x.value));
  return (
    <ul className="rl-barlist">
      {rows.map((x) => (
        <li key={x.key}>
          <div className="rl-barlist__top"><span>{x.label}</span><span>{x.text}</span></div>
          <span className="rl-bar" aria-hidden="true"><span className="rl-bar__fill" style={{ ["--v" as string]: Math.max(0, x.value) / max }} /></span>
        </li>
      ))}
    </ul>
  );
}

/** Money breakdown rows from the API ({key, label, paise}) as bars; one below zero draws no bar but keeps its sign. */
export const moneyBars = (rows: { key: string; label: string; paise: number }[]): Bar[] =>
  rows.map((r) => ({ key: r.key || r.label, label: r.label, value: r.paise, text: signedRupees(r.paise) }));

/** A titled bar list inside a report card, or nothing when there is nothing to compare. */
export function Bars({ title, rows }: { title: string; rows: Bar[] }) {
  if (!rows.length) return null;
  return <><p className="rl-report__sub">{title}</p><BarList rows={rows} /></>;
}
