/* Each report as plain rows, the same ones its screen shows: the CSV and the print page are built from these. */
import type { AttendanceReport, ExpensesReport, MembersReport, MoneyReport, RevenueReport, TasksReport } from "@/api/gen/model";

import { plainRupees, toCsv } from "./csv";
import { PAY_METHOD, STATUS_LABEL } from "./format";

/** One line of a report: which section it's in, what it is, and an amount or a count. */
export type ReportRow = { section: string; date?: string; item: string; detail?: string; paise?: number; count?: number };

const MOVE_KIND: Record<string, string> = { deposit: "Deposit", withdrawal: "Withdrawal", transfer: "Transfer" };
const STATUSES = ["active", "expiring", "due", "frozen", "expired", "none"] as const;

type Named = { key: string; label: string; paise: number };
const named = (section: string, rows: Named[]): ReportRow[] => rows.map((r) => ({ section, item: r.label, paise: r.paise }));

export function revenueRows(r: RevenueReport): ReportRow[] {
  return [
    { section: "Totals", item: "Revenue", detail: "Collected less refunds", paise: r.totals.revenue_paise },
    { section: "Totals", item: "Collected", paise: r.totals.collected_paise },
    { section: "Totals", item: "Refunded", paise: r.totals.refunds_paise, count: r.totals.refunds },
    { section: "Totals", item: "Members owing now", paise: r.dues.total_paise, count: r.dues.members },
    ...r.series.map((d) => ({ section: "By day", date: d.date, item: "Revenue", paise: d.revenue_paise })),
    ...named("By plan", r.by_plan),
    ...named("By method", r.by_method),
    ...named("By branch", r.by_branch),
    ...r.refund_list.map((x) => ({
      section: "Refunds", date: x.on, item: x.member_name, detail: [x.plan, PAY_METHOD[x.method], x.branch_name, x.reason].join(" · "), paise: x.amount_paise,
    })),
  ];
}

export function expensesRows(r: ExpensesReport): ReportRow[] {
  return [
    { section: "Totals", item: "Spent", detail: "Salaries and bills included", paise: r.totals.spent_paise, count: r.totals.count },
    ...r.series.map((d) => ({ section: "By day", date: d.date, item: "Spent", paise: d.spent_paise })),
    ...named("By category", r.by_category),
    ...named("By method", r.by_method),
    ...named("By branch", r.by_branch),
    ...r.bills.rows.map((b) => ({ section: "Bills paid", date: b.paid_on, item: b.name, detail: `Due ${b.due_on}`, paise: b.amount_paise })),
    ...r.salaries.people.map((p) => ({ section: "Salaries paid", item: p.name, paise: p.paid_paise, count: p.payments })),
    { section: "Still owed now", item: "Bills", detail: r.owed.overdue_bills ? `${r.owed.overdue_bills} overdue` : undefined, paise: r.owed.bills_paise, count: r.owed.bills },
    { section: "Still owed now", item: "Salaries", paise: r.owed.salaries_paise, count: r.owed.salaries },
  ];
}

export function moneyRows(r: MoneyReport): ReportRow[] {
  const t = r.totals;
  return [
    { section: "Totals", item: "Cash in hand", detail: "Opening", paise: t.cash_opening_paise },
    { section: "Totals", item: "Cash in hand", detail: "Closing", paise: t.cash_closing_paise },
    { section: "Totals", item: "Bank", detail: "Opening", paise: t.bank_opening_paise },
    { section: "Totals", item: "Bank", detail: "Closing", paise: t.bank_closing_paise },
    { section: "Totals", item: "Total funds", detail: "Opening", paise: t.opening_paise },
    { section: "Totals", item: "Total funds", detail: "Closing", paise: t.closing_paise },
    ...r.accounts.flatMap((a) => [
      { section: "Accounts", item: a.name, detail: "Opening", paise: a.opening_paise },
      { section: "Accounts", item: a.name, detail: "Came in", paise: a.in_paise },
      { section: "Accounts", item: a.name, detail: "Went out", paise: -a.out_paise },
      { section: "Accounts", item: a.name, detail: "Closing", paise: a.closing_paise },
    ]),
    ...r.moves.rows.map((m) => ({
      section: "Money moves", date: m.on, item: MOVE_KIND[m.kind] ?? m.kind,
      detail: [[m.from_name, m.to_name].filter(Boolean).join(" to "), m.note].filter(Boolean).join(" · "), paise: m.amount_paise,
    })),
    ...r.counts.rows.map((c) => ({
      section: "Cash counts", date: c.day, item: c.branch_name,
      detail: `Counted ${plainRupees(c.counted_paise)}, expected ${plainRupees(c.expected_paise)}${c.difference_paise ? (c.settled ? ", settled" : ", not settled") : ""}`,
      paise: c.difference_paise,
    })),
    ...r.accounts.flatMap((a) => (a.reconciled ? [{ section: "Reconciled", date: a.reconciled.up_to, item: a.name, detail: `By ${a.reconciled.by_name}`, paise: a.reconciled.bank_balance_paise }] : [])),
  ];
}

export function membersRows(r: MembersReport, to: string): ReportRow[] {
  return [
    { section: "Totals", item: "New members", count: r.totals.new },
    { section: "Totals", item: "Renewals", count: r.totals.renewals },
    { section: "Totals", item: "Plans ran out, not renewed", count: r.totals.lapsed },
    ...STATUSES.map((s) => ({ section: `Status on ${to}`, item: STATUS_LABEL[s]!, count: r.statuses[s] })),
    ...r.series.map((d) => ({ section: "By day", date: d.date, item: "New members", count: d.new })),
    ...r.branches.flatMap((b) => [
      { section: "By branch", item: b.name, detail: "New members", count: b.new },
      { section: "By branch", item: b.name, detail: "Renewals", count: b.renewals },
      { section: "By branch", item: b.name, detail: `Active on ${to}`, count: b.active },
    ]),
  ];
}

export function attendanceRows(r: AttendanceReport): ReportRow[] {
  const t = r.totals;
  return [
    { section: "Totals", item: "Members", count: t.member },
    { section: "Totals", item: "Trainers", count: t.trainer },
    { section: "Totals", item: "Receptionists", count: t.receptionist },
    { section: "Totals", item: "Admins", count: t.admin },
    ...r.series.flatMap((d) => [
      { section: "By day", date: d.date, item: "Members", count: d.member },
      { section: "By day", date: d.date, item: "Staff", count: d.staff },
    ]),
    ...r.sessions.flatMap((s) => [
      { section: "By session", item: s.session, detail: "Members", count: s.member },
      { section: "By session", item: s.session, detail: "Staff", count: s.trainer + s.receptionist + s.admin },
    ]),
    ...r.branches.flatMap((b) => [
      { section: "By branch", item: b.name, detail: "Members", count: b.member },
      { section: "By branch", item: b.name, detail: "Staff", count: b.staff },
    ]),
  ];
}

export function tasksRows(r: TasksReport): ReportRow[] {
  const t = r.totals;
  return [
    { section: "Totals", item: "Due", count: t.total },
    { section: "Totals", item: "Done", count: t.done },
    { section: "Totals", item: "In progress", count: t.doing },
    { section: "Totals", item: "To do", count: t.todo },
    { section: "Totals", item: "Overdue", count: t.overdue },
    ...r.people.map((p) => ({ section: "By person", item: p.name, detail: `${p.done} done, ${p.overdue} overdue`, count: p.total })),
    ...r.late.map((x) => ({ section: "Oldest overdue", date: x.due_date, item: x.title, detail: x.assignee_name })),
  ];
}

export type ReportMeta = { category: string; gym: string; branch: string; from: string; to: string };

/** A report for a spreadsheet: what it is in the first lines, one header row, then its rows. Amounts in plain rupees
 *  with two decimals, no ₹ and no grouping, so the sheet can add them up. */
export function reportCsv(meta: ReportMeta, rows: ReportRow[]) {
  return toCsv([
    ["Report", meta.category], ["Gym", meta.gym], ["Branch", meta.branch], ["From", meta.from], ["To", meta.to], [],
    ["Section", "Date", "Item", "Detail", "Amount (Rs)", "Count"],
    ...rows.map((r) => [r.section, r.date ?? "", r.item, r.detail ?? "", r.paise === undefined ? "" : plainRupees(r.paise), r.count ?? ""]),
  ]);
}

/** "Cash and bank 2026-10-12 to 2026-10-18.csv" */
export const reportFile = (category: string, from: string, to: string) => `${category} ${from} to ${to}.csv`;

