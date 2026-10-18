"use client";
/* A report category as a record screen (DetailBar with Download, the period, its sections) and as a page to print. */
import { BarChart3, Download, FileSpreadsheet, Printer } from "lucide-react";
import Link from "next/link";
import { Fragment, useState } from "react";

import { DetailBar } from "@/components/shell";
import { Empty, Icon, Sheet, SkeletonRows } from "@/components/ui";
import { ApiError } from "@/lib/api";
import { download } from "@/lib/csv";
import { day, dayShort } from "@/lib/format";
import { reportCsv, reportFile, type ReportRow } from "@/lib/report-rows";
import { categoryName, type Category } from "@/lib/reports";
import { useSession } from "@/lib/session";

import { signedRupees } from "./parts";
import { ReportControls, type ReportRange } from "./range";

/** What a generated report hook answers. */
export type ReportQuery<T> = { data?: { data: T }; isError: boolean; error: unknown; refetch: () => unknown };

type Screen<T> = {
  r: ReportRange; slug: Category; q: ReportQuery<T>;
  /** The rows the CSV and the print page carry: the same ones the sections show. */
  rows: (d: T) => ReportRow[];
  /** Nothing happened in these days: say so instead of a screen of zeros, with the way out (3 months by default). */
  empty?: { when: (d: T) => boolean } & Nothing;
  children: (d: T) => React.ReactNode;
};

type Nothing = { title: string; text: string; action?: React.ReactNode };

const qs = (search: string) => (search ? `?${search}` : "");

export function ReportScreen<T>({ r, slug, q, rows, empty, children }: Screen<T>) {
  const [sheet, setSheet] = useState(false);
  const d = q.data?.data;
  const error = q.error instanceof ApiError ? q.error : null;
  return (
    <div className="rl-app rl-root" data-rscreen="reports">
      <DetailBar title={categoryName(slug)} back={`/reports${qs(r.search)}`} action={
        <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Download" aria-haspopup="dialog" disabled={!d} onClick={() => setSheet(true)}>
          <Icon as={Download} />
        </button>
      } />
      <main className="rl-app__main">
        <ReportControls r={r} meta error={error} />
        <ReportBody r={r} q={q} error={error} empty={empty && d && empty.when(d) ? empty : undefined}>{d && children(d)}</ReportBody>
      </main>
      {d && <DownloadSheet open={sheet} onClose={() => setSheet(false)} r={r} slug={slug} rows={() => rows(d)} />}
    </div>
  );
}

/** Loading, failed, nothing to show, or the report. Only admins see reports; the API refuses everyone else too. */
export function ReportBody<T>({ r, q, error, empty, children }: {
  r: ReportRange; q: ReportQuery<T>; error: ApiError | null; empty?: Nothing; children: React.ReactNode;
}) {
  if (!r.isAdmin) {
    return <Empty icon={BarChart3} title="Reports are for admins" text="Ask an admin of your gym for the figures you need."><Link className="rl-button rl-button--secondary" href="/home">Go Home</Link></Empty>;
  }
  if (r.invalid) return null; // the custom days say what to change
  if (q.isError) {
    return (
      <Empty icon={BarChart3} title="This report didn't load" text={error?.message ?? "Check your connection and try again."}>
        <button className="rl-button rl-button--secondary" type="button" onClick={() => q.refetch()}>Try Again</button>
      </Empty>
    );
  }
  if (!q.data) return <SkeletonRows n={6} />;
  if (empty) {
    return (
      <Empty icon={BarChart3} title={empty.title} text={empty.text}>
        {empty.action ?? (r.period !== "3m" && <button className="rl-button rl-button--secondary" type="button" onClick={() => r.go({ period: "3m" })}>Show 3 Months</button>)}
      </Empty>
    );
  }
  return <>{children}</>;
}

function DownloadSheet({ open, onClose, r, slug, rows }: { open: boolean; onClose: () => void; r: ReportRange; slug: Category; rows: () => ReportRow[] }) {
  const { role } = useSession();
  const name = categoryName(slug);
  const csv = () => {
    download(reportFile(name, r.from, r.to), reportCsv({ category: name, gym: role.gym_name, branch: r.branchName, from: r.from, to: r.to }, rows()));
    onClose();
  };
  return (
    <Sheet open={open} onClose={onClose} title="Download">
      <p className="rl-row__meta" style={{ marginTop: 0 }}>{name}, {day(r.from)} to {day(r.to)}, {r.branch === null ? "all branches" : r.branchName}.</p>
      <ul className="rl-sheet__list">
        <li><button className="rl-sheet__item" type="button" onClick={csv}>
          <span className="rl-chipicon"><Icon as={FileSpreadsheet} size="sm" /></span><span className="rl-sheet__text">Download CSV</span>
        </button></li>
        <li><Link className="rl-sheet__item" href={`/reports/${slug}/print${qs(r.search)}`}>
          <span className="rl-chipicon"><Icon as={Printer} size="sm" /></span><span className="rl-sheet__text">Print or PDF</span>
        </Link></li>
      </ul>
    </Sheet>
  );
}

/** One row on paper: when and what on the left; the amount or count on the right, never broken mid-figure. */
const label = (x: ReportRow) => [x.date && dayShort(x.date), x.item, x.detail].filter(Boolean).join(", ");
const value = (x: ReportRow) => [x.paise !== undefined && signedRupees(x.paise), x.count !== undefined && x.count.toLocaleString("en-IN")].filter(Boolean).join(" · ");

/** A report to print or save as a PDF from the browser, like the statement: on plain paper, with the app bar, the
 *  button and the tab bar left out (rl-noprint). */
export function ReportPrint<T>({ r, slug, q, rows }: Pick<Screen<T>, "r" | "slug" | "q" | "rows">) {
  const { role } = useSession();
  const d = q.data?.data;
  const sections = new Map<string, ReportRow[]>();
  for (const x of d ? rows(d) : []) sections.set(x.section, [...(sections.get(x.section) ?? []), x]);
  return (
    <div className="rl-app rl-root" data-rscreen="reports">
      <div className="rl-noprint"><DetailBar title="Print report" back={`/reports/${slug}${qs(r.search)}`} /></div>
      <main className="rl-app__main">
        {!r.isAdmin || q.isError ? <ReportBody r={r} q={q} error={q.error instanceof ApiError ? q.error : null}>{null}</ReportBody> : !d ? <SkeletonRows n={6} /> : (
          <>
            <section className="rl-section">
              <div className="rl-card rl-card--pad">
                <p className="rl-row__meta" style={{ margin: 0 }}>{role.gym_name}</p>
                <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>{categoryName(slug)}</h2>
                <dl className="rl-facts">
                  <dt>Branch</dt><dd>{r.branchName}</dd>
                  <dt>Days</dt><dd>{day(r.from)} to {day(r.to)}</dd>
                </dl>
              </div>
            </section>
            {[...sections].map(([title, lines]) => (
              <section className="rl-section" key={title} aria-label={title}>
                <div className="rl-card rl-card--pad">
                  <h2 className="rl-section__title" style={{ margin: 0 }}>{title}</h2>
                  <dl className="rl-facts">{lines.map((x, i) => <Fragment key={i}><dt>{label(x)}</dt><dd>{value(x)}</dd></Fragment>)}</dl>
                </div>
              </section>
            ))}
            <section className="rl-section rl-noprint">
              <button className="rl-button rl-button--block" type="button" onClick={() => window.print()}><Icon as={Printer} size="sm" />Print Report</button>
              <p className="rl-field__hint">To save it as a PDF, choose Save as PDF in the print window.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
