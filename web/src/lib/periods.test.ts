import { describe, expect, it } from "vitest";

import { historyPeriod, rangeOf } from "./periods";

describe("rangeOf", () => {
  const today = "2026-10-24";
  it("works out each period's first and last day", () => {
    expect(rangeOf("today", today, null, null)).toEqual([today, today]);
    expect(rangeOf("yesterday", today, null, null)).toEqual(["2026-10-23", "2026-10-23"]);
    expect(rangeOf("7d", today, null, null)).toEqual(["2026-10-18", today]);
    expect(rangeOf("month", today, null, null)).toEqual(["2026-10-01", today]);
    expect(rangeOf("90d", today, null, null)).toEqual(["2026-07-27", today]);
    expect(rangeOf("year", today, null, null)).toEqual(["2026-01-01", today]);
  });
  it("has no days for all time", () => {
    expect(rangeOf("all", today, "2026-01-01", "2026-02-01")).toEqual(["", ""]);
  });
  it("takes the custom days asked for, filling in what's missing", () => {
    expect(rangeOf("custom", today, "2026-09-01", "2026-09-30")).toEqual(["2026-09-01", "2026-09-30"]);
    expect(rangeOf("custom", today, "2026-09-01", null)).toEqual(["2026-09-01", "2026-09-01"]);
    expect(rangeOf("custom", today, null, null)).toEqual([today, today]);
  });
});

describe("historyPeriod", () => {
  it("keeps a history period from the address, else all time", () => {
    expect(historyPeriod("90d")).toBe("90d");
    expect(historyPeriod("yesterday")).toBe("all");
    expect(historyPeriod(null)).toBe("all");
  });
});
