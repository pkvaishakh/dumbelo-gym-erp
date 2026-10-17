import { describe, expect, it } from "vitest";

import { monthLabel, plural, rangeLabel, rupees, rupeesShort, seen, toPaise, trend, until } from "./format";
import { paged, pages } from "./hooks";
import { keyUrl } from "./query";

describe("money", () => {
  it("shows rupees with Indian grouping and no paise when there are none", () => {
    expect(rupees(15000000)).toBe("₹1,50,000");
    expect(rupees(150050)).toBe("₹1,500.5");
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
