"use client";
/* The design system's one-series chart (rl-chart): bars for a short run of days with the latest in volt, a line for
   longer ones with the latest point in volt and its value beside it. Tap, hover or focus a point to read it. */
import { useState } from "react";

export type ChartPoint = {
  /** Under the axis, when there is room: "Mon", "Today", "4 Oct" */
  tick: string;
  /** The point's name in the tooltip: "Mon 28 Sep" */
  label: string;
  value: number;
  /** The value in words: "₹38,200", "3 new members" */
  text: string;
};

/** A round top for the axis: 0, half of it and it. */
function niceMax(n: number) {
  if (n <= 4) return 4;
  const step = 10 ** Math.floor(Math.log10(n));
  const top = [1, 2, 2.5, 4, 5, 10].map((m) => m * step).find((m) => m >= n)!;
  return top % 2 ? top * 2 : top;
}

const TICKS = 4;

export function Chart({ points, label, axis, cap, latest = true, line }: {
  points: ChartPoint[]; label: string;
  /** Labels the y axis: rupeesShort for money, String for counts. */
  axis: (n: number) => string;
  /** Short value over the latest bar or beside the latest point. */
  cap?: (n: number) => string;
  /** The last point is the latest day (today or the range's end): mark it in volt. */
  latest?: boolean;
  /** Draw a line instead of bars (longer ranges). */
  line?: boolean;
}) {
  const [active, setActive] = useState<number | null>(null);
  const n = points.length;
  const top = niceMax(Math.max(0, ...points.map((p) => p.value)));
  const at = (i: number) => (line ? (n === 1 ? 0.5 : i / (n - 1)) : (i + 0.5) / n);
  const v = (i: number) => points[i]!.value / top;
  const last = n - 1;
  // Free ticks on long runs: about four, always the first and last.
  const ticks = n <= 7 ? points.map((p, i) => ({ i, t: p.tick })) : Array.from(new Set(Array.from({ length: TICKS }, (_, k) => Math.round((k * last) / (TICKS - 1))))).map((i) => ({ i, t: points[i]!.tick }));
  const path = points.map((_, i) => `${(at(i) * 100).toFixed(2)},${(100 - v(i) * 100).toFixed(2)}`).join(" ");

  return (
    <div className="rl-chart" role="group" aria-label={label}>
      <div className="rl-chart__y" aria-hidden="true">
        {[0, 0.5, 1].map((p) => <span key={p} style={{ ["--p" as string]: p }}>{axis(top * p)}</span>)}
      </div>
      <div className="rl-chart__plot" onPointerLeave={() => setActive(null)}>
        <div className="rl-chart__grid" aria-hidden="true">{[0, 0.5, 1].map((p) => <span key={p} style={{ ["--p" as string]: p }} />)}</div>
        {line && n > 1 && (
          <svg className="rl-chart__line" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <polygon className="rl-chart__area" points={`0,100 ${path} 100,100`} />
            <polyline className="rl-chart__stroke" points={path} />
          </svg>
        )}
        <div className={`rl-chart__cols${active !== null ? " has-active" : ""}`}>
          {points.map((p, i) => (
            <button
              key={i} type="button" aria-label={`${p.label}: ${p.text}`}
              className={`rl-chart__col${!line && latest && i === last ? " is-today" : ""}${active === i ? " is-active" : ""}`}
              style={{ ["--v" as string]: v(i), ["--x" as string]: at(i) }}
              onPointerEnter={() => setActive(i)} onFocus={() => setActive(i)} onBlur={() => setActive(null)} onClick={() => setActive(i)}
            >
              {!line && <span className="rl-chart__bar" />}
              {!line && cap && latest && i === last && p.value > 0 && <span className="rl-chart__cap">{cap(p.value)}</span>}
            </button>
          ))}
        </div>
        {line && latest && <span className="rl-chart__dot" style={{ ["--x" as string]: at(last), ["--v" as string]: v(last) }} aria-hidden="true" />}
        {line && latest && cap && active === null && points[last]!.value > 0 && <span className="rl-chart__end" style={{ ["--v" as string]: v(last) }} aria-hidden="true">{cap(points[last]!.value)}</span>}
        {line && active !== null && <span className="rl-chart__marker is-on" style={{ ["--x" as string]: at(active), ["--v" as string]: v(active) }} aria-hidden="true" />}
        <div
          className={`rl-chart__tip${active !== null ? " is-on" : ""}`} role="status"
          style={active !== null ? { left: `clamp(56px, ${at(active) * 100}%, calc(100% - 56px))`, bottom: `calc(${v(active) * 100}% + 16px)` } : undefined}
        >
          {active !== null && <><strong>{points[active]!.label}</strong> {points[active]!.text}</>}
        </div>
      </div>
      <div className={`rl-chart__x${n > 7 ? " rl-chart__x--free" : ""}`} aria-hidden="true">
        {ticks.map(({ i, t }) => (
          <span key={i} className={latest && i === last && n <= 7 ? "is-today" : undefined} style={n > 7 ? { ["--x" as string]: at(i) } : undefined}>{t}</span>
        ))}
      </div>
    </div>
  );
}
