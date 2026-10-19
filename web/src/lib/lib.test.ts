import { describe, expect, it } from "vitest";

import { branchesOf, countDifference, gymToday, INVOICE_STATUS, invoiceState, lastDigits, monthLabel, moveLabel, ordinal, plural, rangeLabel, recentMonths, rupees, rupeesShort, seen, SLUG_RULE, slugify, toPaise, took, trend, until } from "./format";
import { plainRupees, statementCsv, toCsv } from "./csv";
import { paged, pages } from "./hooks";
import { keyUrl } from "./query";

describe("money", () => {
  it("shows rupees with Indian grouping and no paise when there are none", () => {
    expect(rupees(15000000)).toBe("₹1,50,000");
    expect(rupees(150050)).toBe("₹1,500.50"); // two paise digits, like the API's rupees()
    expect(rupees(90)).toBe("₹0.90");
    expect(rupees(null)).toBe("₹0");
  });
  it("turns typed rupees into whole paise", () => {
    expect(toPaise("1,500")).toBe(150000);
    expect(toPaise("₹99.99")).toBe(9999);
    expect(toPaise("abc")).toBe(0);
  });
  it("counts in words", () => {
    expect(plural(1, "member")).toBe("1 member");
    expect(plural(1200, "member")).toBe("1,200 members");
  });
});

describe("cash counts", () => {
  it("says how far the drawer is from what it should hold", () => {
    expect(countDifference(-20000)).toBe("₹200 short");
    expect(countDifference(5000)).toBe("₹50 over");
    expect(countDifference(0)).toBe("Matches");
  });
});

describe("the gym's day", () => {
  it("is the date in the gym's time zone, not the device's", () => {
    const lateUtc = new Date("2026-10-18T20:00:00Z"); // 1:30 AM on the 19th in India
    expect(gymToday("Asia/Kolkata", lateUtc)).toBe("2026-10-19");
    expect(gymToday("UTC", lateUtc)).toBe("2026-10-18");
  });
});

describe("when a device was last seen", () => {
  it("says Never for a device that has never punched", () => {
    expect(seen(null)).toBe("Never");
    expect(seen(undefined)).toBe("Never");
    expect(seen("")).toBe("Never");
  });
  it("counts back from now for one that has", () => {
    expect(seen(new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString())).toBe("2 hours ago");
  });
});

describe("when access runs out", () => {
  const now = new Date("2026-10-16T12:00:00");
  it("gives the clock time on the same day", () => {
    expect(until("2026-10-16T18:00:00", now)).toBe("6:00 PM");
  });
  it("names the day when it is a later one", () => {
    expect(until("2026-10-18T09:30:00", now)).toBe("9:30 AM on 18 Oct");
  });
});

describe("paging", () => {
  const page = (next: string | null, results: number[]) => ({ data: { count: 120, next, results } });

  it("asks for the next page by its offset, and stops at the end", () => {
    expect(paged.getNextPageParam(page("http://localhost:8000/api/members/?limit=50&offset=50", []))).toBe(50);
    expect(paged.getNextPageParam(page("/api/members/?offset=100", []))).toBe(100);
    expect(paged.getNextPageParam(page(null, []))).toBeUndefined();
  });
  it("joins the loaded pages and keeps the full count", () => {
    expect(pages({ data: { pages: [page("x", [1, 2]), page(null, [3])] } })).toEqual({ rows: [1, 2, 3], count: 120 });
    expect(pages({})).toEqual({ rows: [], count: 0 });
  });
});

describe("cache keys", () => {
  it("finds the URL in plain and paged query keys, so a change refreshes both", () => {
    expect(keyUrl(["/api/members/", { status: "due" }])).toBe("/api/members/");
    expect(keyUrl(["infinite", "/api/members/", {}])).toBe("/api/members/");
    expect(keyUrl([42])).toBeUndefined();
  });
});

describe("reports", () => {
  it("shortens rupees in Indian units for chart labels", () => {
    expect(rupeesShort(85000)).toBe("₹850");
    expect(rupeesShort(4865000)).toBe("₹48.7k");
    expect(rupeesShort(12000000)).toBe("₹1.2L");
    expect(rupeesShort(340000000)).toBe("₹34L");
    expect(rupeesShort(3400000000)).toBe("₹3.4Cr");
  });
  it("names a range of days, with years only when they aren't this year", () => {
    const now = new Date(2026, 9, 17);
    expect(rangeLabel("2026-09-28", "2026-10-04", now)).toBe("28 Sep to 4 Oct");
    expect(rangeLabel("2025-12-28", "2026-01-03", now)).toBe("28 Dec 2025 to 3 Jan 2026");
    expect(rangeLabel("2026-10-04", "2026-10-04", now)).toBe("4 Oct");
  });
  it("compares a figure with the period before it in words", () => {
    expect(trend(109, 100, 7)).toEqual({ dir: "up", text: "+9% vs previous 7 days" });
    expect(trend(80, 100, 30)).toEqual({ dir: "down", text: "-20% vs previous 30 days" });
    expect(trend(5, 0, 7)).toEqual({ dir: "up", text: "Up from 0 vs previous 7 days" });
    expect(trend(0, 0, 7)).toEqual({ dir: "flat", text: "Same as previous 7 days" });
    expect(trend(1001, 1000, 7).text).toBe("+0% vs previous 7 days");
  });
});

describe("monthLabel", () => {
  it("names the month a payslip is for", () => {
    expect(monthLabel("2026-10-01")).toBe("October 2026");
    expect(monthLabel("2027-01")).toBe("January 2027");
  });
});

describe("money moves", () => {
  it("names a move by the accounts it went between", () => {
    expect(moveLabel({ kind: "transfer", from_kind: "cash", to_kind: "bank" })).toBe("Cash to bank");
    expect(moveLabel({ kind: "transfer", from_kind: "bank", to_kind: "cash" })).toBe("Bank to cash");
    expect(moveLabel({ kind: "transfer", from_kind: "cash", to_kind: "cash" })).toBe("Cash between branches");
    expect(moveLabel({ kind: "transfer", from_kind: "bank", to_kind: "bank" })).toBe("Bank to bank");
    expect(moveLabel({ kind: "deposit", to_kind: "bank" })).toBe("Deposit");
    expect(moveLabel({ kind: "withdrawal", from_kind: "cash" })).toBe("Withdrawal");
  });
  it("shows only the end of an account number", () => {
    expect(lastDigits("50200012345678")).toBe("•• 5678");
    expect(lastDigits("")).toBe("");
  });
});

describe("recentMonths", () => {
  it("lists this month first, then the ones before it", () => {
    const months = recentMonths(3, new Date(2026, 0, 15));
    expect(months).toEqual([
      { value: "2026-01", label: "This month" },
      { value: "2025-12", label: "Dec 2025" },
      { value: "2025-11", label: "Nov 2025" },
    ]);
  });
});

describe("statement CSV", () => {
  it("writes plain rupees the sheet can add up, and quotes what needs it", () => {
    expect(plainRupees(150000)).toBe("1500.00");
    expect(plainRupees(-8500050)).toBe("-85000.50");
    expect(plainRupees(5)).toBe("0.05");
    expect(toCsv([["a,b", 'say "hi"', 3]])).toBe('"a,b","say ""hi""",3\r\n');
  });
  it("opens and closes with the balances, each entry with the balance after it", () => {
    const csv = statementCsv("HDFC current", {
      from: "2026-10-01", to: "2026-10-18", opening_paise: 100000, closing_paise: 230000, in_paise: 150000, out_paise: 20000, cleared_paise: 0, reconciled: null,
      entries: [
        { kind: "payment", id: 1, member: 4, on: "2026-10-02", title: "Ravi", meta: "Payment by UPI", amount_paise: 150000, balance_paise: 250000, ticked: true, reconciled: true },
        { kind: "expense", id: 2, member: null, on: "2026-10-03", title: "BESCOM", meta: "Utilities by UPI", amount_paise: -20000, balance_paise: 230000, ticked: false, reconciled: false },
      ],
    }).split("\r\n");
    expect(csv[1]).toBe("HDFC current,2026-10-01,,Opening balance,,,1000.00,");
    expect(csv[2]).toBe("HDFC current,2026-10-02,Payment,Ravi,Payment by UPI,1500.00,2500.00,Yes");
    expect(csv[3]).toBe("HDFC current,2026-10-03,Expense,BESCOM,Utilities by UPI,-200.00,2300.00,");
    expect(csv[4]).toBe("HDFC current,2026-10-18,,Closing balance,,,2300.00,");
  });
});

describe("gym short names", () => {
  it("suggests one from the gym's name that the API accepts", () => {
    expect(slugify("Iron House, Kochi")).toBe("iron-house-kochi");
    expect(slugify("  Café Fit  ")).toBe("cafe-fit");
    expect(slugify("Gym-".repeat(20))).toHaveLength(39); // cut to 40, then the trailing dash goes
    expect(SLUG_RULE.test(slugify("Pulse Fitness 24x7"))).toBe(true);
  });
  it("refuses what the API refuses", () => {
    expect(SLUG_RULE.test("ab")).toBe(false);
    expect(SLUG_RULE.test("-iron")).toBe(false);
    expect(SLUG_RULE.test("Iron")).toBe(false);
  });
});

describe("Dumbelo plan", () => {
  it("names the billing day", () => {
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 28].map(ordinal)).toEqual(["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd", "28th"]);
  });
  it("says how much of the quota is in use", () => {
    expect(branchesOf(2, 3)).toBe("2 of 3 branches");
    expect(branchesOf(1, 1)).toBe("1 of 1 branch");
  });
});

describe("Dumbelo invoices", () => {
  it("calls an open invoice past its due day overdue", () => {
    expect(invoiceState({ status: "open", overdue: true })).toBe("overdue");
    expect(invoiceState({ status: "open", overdue: false })).toBe("open");
    expect(invoiceState({ status: "paid", overdue: false })).toBe("paid");
    expect(invoiceState({ status: "void", overdue: false })).toBe("void");
  });
  it("has a badge for every state", () => {
    expect(Object.keys(INVOICE_STATUS).sort()).toEqual(["open", "overdue", "paid", "void"]);
  });
});

describe("how long a job took", () => {
  it("says it in words", () => {
    expect(took(0.4)).toBe("under a second");
    expect(took(1)).toBe("1 second");
    expect(took(12.4)).toBe("12 seconds");
    expect(took(60)).toBe("1 min");
    expect(took(185.2)).toBe("3 min 5 s");
  });
});
