import { describe, expect, it } from "vitest";

import { daysLabel, gymLogFilters, gymLogParams, gymLogUrl, hourLabel, narrowedBy, NO_GYM_FILTERS, recentMonths, whenLabel } from "./messages";

describe("hourLabel", () => {
  it("says a 24-hour clock hour the way people do", () => {
    expect(hourLabel(0)).toBe("12 AM");
    expect(hourLabel(6)).toBe("6 AM");
    expect(hourLabel(12)).toBe("12 PM");
    expect(hourLabel(23)).toBe("11 PM");
  });
});

describe("daysLabel", () => {
  it("lists the days furthest first, each once", () => {
    expect(daysLabel([3, 7])).toBe("7 and 3 days");
    expect(daysLabel([10, 2, 5, 5])).toBe("10, 5 and 2 days");
  });
  it("says one day as a day", () => {
    expect(daysLabel([1])).toBe("1 day");
    expect(daysLabel([7, 1])).toBe("7 days and 1 day");
    expect(daysLabel([14])).toBe("14 days");
    expect(daysLabel([])).toBe("");
  });
});

describe("whenLabel", () => {
  it("says when a message at an hour goes out", () => {
    expect(whenLabel({ kind: "plan_ending", hour: 6, days_ahead: [7, 3] })).toBe("7 and 3 days before a plan ends, at 6 AM");
    expect(whenLabel({ kind: "plan_ends_today", hour: 9, days_ahead: null })).toBe("The day a plan ends, at 9 AM");
  });
  it("says what sends the others", () => {
    expect(whenLabel({ kind: "payment_received", hour: null, days_ahead: null })).toBe("When the desk records a payment");
  });
});

describe("the gym's message log filters", () => {
  const read = (q: string) => gymLogFilters(new URLSearchParams(q));

  it("reads the address and writes it back without the defaults", () => {
    const f = read("status=failed&kind=payment_due&from=2026-10-01&extra=1");
    expect(f).toEqual({ ...NO_GYM_FILTERS, status: "failed", kind: "payment_due", from: "2026-10-01" });
    expect(gymLogUrl(f)).toBe("/messages?status=failed&kind=payment_due&from=2026-10-01");
    expect(gymLogUrl(NO_GYM_FILTERS)).toBe("/messages");
  });

  it("asks the API only for filters it knows, so a mistyped address still loads", () => {
    expect(gymLogParams(read("status=lost&kind=birthday&recipient=staff"), "")).toEqual({ recipient: "staff" });
    expect(gymLogParams(read("status=all&to=2026-10-05"), "ravi")).toEqual({ q: "ravi", to: "2026-10-05" });
  });

  it("says what narrows the list", () => {
    expect(narrowedBy(read("kind=payment_due&recipient=member&to=2026-10-05"))).toBe("payment due, members, some days");
    expect(narrowedBy(read("status=failed"))).toBe("");
  });
});

describe("recentMonths", () => {
  it("counts back across a new year, newest first", () => {
    expect(recentMonths("2026-02", 4)).toEqual(["2026-02", "2026-01", "2025-12", "2025-11"]);
    expect(recentMonths("2026-10")).toHaveLength(24);
  });
});
