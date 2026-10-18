import { describe, expect, it } from "vitest";

import type { AttendanceReport, ExpensesReport, MembersReport, MoneyReport, RevenueReport, TasksReport } from "@/api/gen/model";

import { gymToday } from "./format";
import { attendanceRows, expensesRows, membersRows, moneyRows, reportCsv, reportFile, revenueRows, tasksRows, type ReportRow } from "./report-rows";
import { changeSince, earliest, rangeError, rangeOf } from "./reports";

describe("report periods", () => {
  const today = "2026-10-18";
  it("end on the gym's today", () => {
    expect(rangeOf("7d", today)).toEqual(["2026-10-12", today]);
    expect(rangeOf("30d", today)).toEqual(["2026-09-19", today]);
    expect(rangeOf("month", today)).toEqual(["2026-10-01", today]);
    expect(rangeOf("3m", today)).toEqual(["2026-07-19", today]);
  });
  it("take the gym's day, not the device's: late evening in India is already tomorrow there", () => {
    const lateUtc = new Date("2026-10-18T20:00:00Z");
    expect(rangeOf("7d", gymToday("Asia/Kolkata", lateUtc))).toEqual(["2026-10-13", "2026-10-19"]);
  });
  it("keep custom days, and fall back to 7 days for missing or broken ones", () => {
    expect(rangeOf("custom", today, "2026-09-01", "2026-09-30")).toEqual(["2026-09-01", "2026-09-30"]);
    expect(rangeOf("custom", today, null, "nonsense")).toEqual(["2026-10-12", today]);
  });
  it("3 months back clamps month ends the way the API does", () => {
    expect(earliest("2026-05-31")).toBe("2026-03-01"); // 31 Feb doesn't exist: 28 Feb, so from 1 Mar
    expect(earliest("2026-11-30")).toBe("2026-08-31");
    expect(earliest("2024-05-30")).toBe("2024-03-01"); // leap year: 29 Feb, so from 1 Mar
    expect(rangeOf("3m", "2026-05-31")).toEqual(["2026-03-01", "2026-05-31"]);
  });
});

describe("custom range check", () => {
  const today = "2026-10-18";
  it("allows up to 3 calendar months and says so in the API's words past that", () => {
    expect(rangeError("2026-07-19", today, today)).toBeNull();
    expect(rangeError("2026-07-18", today, today)).toEqual({ field: "from", message: "Pick a range of 3 months or less" });
    expect(rangeError("2026-03-01", "2026-05-31", today)).toBeNull();
    expect(rangeError("2026-02-28", "2026-05-31", today)?.field).toBe("from");
  });
  it("refuses days after today, and a start after the end", () => {
    expect(rangeError("2026-10-12", "2026-10-19", today)).toEqual({ field: "to", message: "Pick today or an earlier day" });
    expect(rangeError("2026-10-15", "2026-10-14", today)?.message).toBe("Pick a start date on or before the end date");
  });
  it("puts a balance against what it held before the first day", () => {
    expect(changeSince(1_20_000_00, 1_00_000_00, "2026-10-12").text).toBe("+₹20,000 since 12 Oct");
    expect(changeSince(90_000_00, 1_00_000_00, "2026-10-12")).toEqual({ dir: "down", text: "−₹10,000 since 12 Oct" });
    expect(changeSince(5, 5, "2026-10-12").dir).toBe("flat");
  });
});

const span = { from: "2026-10-12", to: "2026-10-13", days: 2, previous: { from: "2026-10-10", to: "2026-10-11" } };
const meta = { category: "Revenue", gym: "Iron House", branch: "All branches", from: span.from, to: span.to };
const lines = (rows: ReportRow[]) => reportCsv(meta, rows).trim().split("\r\n");

describe("report CSVs", () => {
  it("open with what the report is, then one header row, amounts in plain rupees", () => {
    const csv = lines([{ section: "Totals", item: "Revenue", detail: "Collected, less refunds", paise: 150050 }]);
    expect(csv.slice(0, 5)).toEqual(["Report,Revenue", "Gym,Iron House", "Branch,All branches", "From,2026-10-12", "To,2026-10-13"]);
    expect(csv[6]).toBe("Section,Date,Item,Detail,Amount (Rs),Count");
    expect(csv[7]).toBe('Totals,,Revenue,"Collected, less refunds",1500.50,');
    expect(reportFile("Cash and bank", span.from, span.to)).toBe("Cash and bank 2026-10-12 to 2026-10-13.csv");
  });

  it("revenue: totals, days, plans and refunds, refunds below zero where they reduce revenue", () => {
    const r: RevenueReport = {
      ...span, totals: { revenue_paise: 100000, collected_paise: 150000, refunds_paise: 50000, refunds: 1 }, before: { revenue_paise: 0 },
      series: [{ date: "2026-10-12", revenue_paise: 0 }, { date: "2026-10-13", revenue_paise: 100000 }],
      by_plan: [{ key: "Monthly", label: "Monthly", paise: 100000 }], by_method: [{ key: "upi", label: "UPI", paise: 150000 }, { key: "cash", label: "Cash", paise: -50000 }],
      by_branch: [], dues: { members: 2, total_paise: 300000 },
      refund_list: [{ id: 1, on: "2026-10-13", member: 9, member_name: "Asha", plan: "Monthly", method: "cash", branch_name: "A", amount_paise: 50000, reason: "Moved away" }],
    };
    const csv = lines(revenueRows(r));
    expect(csv).toContain("Totals,,Revenue,Collected less refunds,1000.00,");
    expect(csv).toContain("Totals,,Members owing now,,3000.00,2");
    expect(csv).toContain("By day,2026-10-13,Revenue,,1000.00,");
    expect(csv).toContain("By method,,Cash,,-500.00,");
    expect(csv).toContain("Refunds,2026-10-13,Asha,Monthly · Cash · A · Moved away,500.00,");
  });

  it("expenses: categories, bills paid, salaries and what is still owed", () => {
    const r: ExpensesReport = {
      ...span, totals: { spent_paise: 790000, count: 3 }, before: { spent_paise: 0 }, series: [{ date: "2026-10-13", spent_paise: 790000 }],
      by_category: [{ key: "salaries", label: "Salaries", paise: 500000 }], by_method: [], by_branch: [],
      bills: { count: 1, paid_paise: 250000, rows: [{ id: 4, name: "Rent", due_on: "2026-10-10", paid_on: "2026-10-13", amount_paise: 250000 }] },
      salaries: { count: 1, paid_paise: 500000, people: [{ id: 3, name: "Neha", paid_paise: 500000, payments: 1 }] },
      owed: { bills: 2, overdue_bills: 1, bills_paise: 120000, salaries: 1, salaries_paise: 1500000 },
    };
    const csv = lines(expensesRows(r));
    expect(csv).toContain("Totals,,Spent,Salaries and bills included,7900.00,3");
    expect(csv).toContain("Bills paid,2026-10-13,Rent,Due 2026-10-10,2500.00,");
    expect(csv).toContain("Salaries paid,,Neha,,5000.00,1");
    expect(csv).toContain("Still owed now,,Bills,1 overdue,1200.00,2");
  });

  it("cash and bank: each account's balances, moves, counts and reconciliations", () => {
    const r: MoneyReport = {
      from: span.from, to: span.to, days: 2,
      totals: { cash_opening_paise: 500000, cash_closing_paise: 430000, bank_opening_paise: 10000000, bank_closing_paise: 10100000, opening_paise: 10500000, closing_paise: 10530000 },
      accounts: [{ id: 1, name: "HDFC current", kind: "bank", is_active: true, opened_on: "2026-01-01", shared_with: ["B"], opening_paise: 10000000, closing_paise: 10100000,
        in_paise: 150000, out_paise: 50000, moved_in_paise: 100000, moved_out_paise: 0, reconciled: { up_to: "2026-10-12", bank_balance_paise: 9990000, by_name: "Meera" } }],
      moves: { count: 1, rows: [{ id: 2, on: "2026-10-13", kind: "transfer", from_name: "A cash", to_name: "HDFC current", amount_paise: 100000, note: "" }] },
      counts: { count: 1, short_paise: 20000, over_paise: 0, to_settle: 1, rows: [{ id: 3, day: "2026-10-13", branch_name: "A", counted_paise: 480000, expected_paise: 500000, difference_paise: -20000, settled: false }] },
    };
    const csv = lines(moneyRows(r));
    expect(csv).toContain("Totals,,Total funds,Closing,105300.00,");
    expect(csv).toContain("Accounts,,HDFC current,Went out,-500.00,");
    expect(csv).toContain("Money moves,2026-10-13,Transfer,A cash to HDFC current,1000.00,");
    expect(csv).toContain('Cash counts,2026-10-13,A,"Counted 4800.00, expected 5000.00, not settled",-200.00,');
    expect(csv).toContain("Reconciled,2026-10-12,HDFC current,By Meera,99900.00,");
  });

  it("members, attendance and tasks: counts in the Count column", () => {
    const m: MembersReport = {
      ...span, totals: { new: 3, renewals: 1, lapsed: 1 }, before: { new: 0, renewals: 0 }, series: [{ date: "2026-10-13", new: 3 }],
      statuses: { total: 3, active: 1, expiring: 1, due: 0, frozen: 0, expired: 1, none: 0 }, branches: [{ id: 1, name: "A", new: 3, renewals: 1, active: 2 }],
    };
    expect(lines(membersRows(m, m.to))).toEqual(expect.arrayContaining([
      "Totals,,\"Plans ran out, not renewed\",,,1", "Status on 2026-10-13,,Expiring,,,1", "By branch,,A,Active on 2026-10-13,,2",
    ]));
    const a: AttendanceReport = {
      ...span, totals: { member: 2, trainer: 1, receptionist: 1, admin: 0 }, before: { member: 0 }, series: [{ date: "2026-10-13", member: 1, staff: 2 }],
      sessions: [{ session: "Morning", member: 1, trainer: 0, receptionist: 1, admin: 0 }], branches: [],
    };
    expect(lines(attendanceRows(a))).toEqual(expect.arrayContaining(["By day,2026-10-13,Staff,,,2", "By session,,Morning,Staff,,1"]));
    const t: TasksReport = {
      ...span, totals: { total: 3, todo: 1, doing: 1, done: 1, overdue: 2 }, before: { done: 0 },
      people: [{ id: 1, name: "Neha", role: "trainer", total: 2, done: 1, overdue: 1 }],
      late: [{ id: 5, title: "Fix the leg press", assignee_name: "Neha", due_date: "2026-10-12", due_time: null, status: "doing" }],
    };
    expect(lines(tasksRows(t))).toEqual(expect.arrayContaining([
      "Totals,,Overdue,,,2", 'By person,,Neha,"1 done, 1 overdue",,2', "Oldest overdue,2026-10-12,Fix the leg press,Neha,,",
    ]));
  });
});
