import { describe, expect, it } from "vitest";

import { plural, rupees, seen, toPaise } from "./format";
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
