import { describe, expect, it } from "vitest";

import { type ChatFacts, memberChats, membershipChat, nextPlanChat, receiptChat, whatsappLink } from "./member-chat";

const base: ChatFacts = {
  name: "Ravi Kumar", code: "M0012", gym: "Iron Temple", today: "2026-10-24",
  plan: { name: "Quarterly", starts: "2026-08-01", ends: "2026-10-31" },
  due: 0, sub: { price_paise: 450000, paid_paise: 450000 }, lastVisit: "2026-10-23",
};
const kinds = (f: ChatFacts) => memberChats(f).map((c) => c.kind);
const text = (f: ChatFacts, kind: string) => memberChats(f).find((c) => c.kind === kind)?.text;

describe("memberChats", () => {
  it("offers only what fits: a paid-up member who came in yesterday", () => {
    expect(kinds(base)).toEqual(["renewal", "membership", "welcome", "blank"]);
    expect(kinds({ ...base, plan: { ...base.plan!, ends: "2026-12-31" } })).toEqual(["membership", "welcome", "blank"]);
  });

  it("asks for what's owed, with the amount for the desk and without it for a trainer", () => {
    expect(text({ ...base, due: 150000 }, "payment_due")).toBe(
      "Hi Ravi, ₹1,500 is still due for your Quarterly plan at Iron Temple. You can pay at the front desk on your next visit. Thank you!");
    const trainer = memberChats({ ...base, due: null, sub: null, paymentDue: true });
    expect(trainer[0]!.text).toBe(
      "Hi Ravi, a payment is still due for your Quarterly plan at Iron Temple. You can pay at the front desk on your next visit. Thank you!");
    expect(trainer.map((c) => c.text).join(" ")).not.toContain("₹");
  });

  it("says how soon a plan ends, or that it has", () => {
    expect(text(base, "renewal")).toContain("ends in 7 days, on 31 Oct 2026");
    expect(text({ ...base, today: "2026-10-30" }, "renewal")).toContain("ends tomorrow.");
    expect(text({ ...base, today: "2026-10-31" }, "renewal")).toContain("ends today.");
    expect(text({ ...base, today: "2026-11-02" }, "renewal")).toBe(
      "Hi Ravi, your Quarterly plan at Iron Temple ended on 31 Oct 2026. Renew it at the front desk to start training again. We'd love to see you back!");
  });

  const next = { name: "Quarterly", starts: "2026-11-01", ends: "2027-01-31", price_paise: 450000, paid_paise: 450000 };

  it("confirms the next plan instead of asking them to renew", () => {
    const f = { ...base, upcoming: [next] };
    expect(kinds(f)).toEqual(["next_plan", "membership", "welcome", "blank"]);
    expect(text(f, "next_plan")).toBe("Hi Ravi, your next plan at Iron Temple is booked: Quarterly, from 1 Nov 2026 to 31 Jan 2027."
      + " It starts right after your current plan ends, so there's no break. It's paid in full. Thank you!");
    expect(text(f, "membership")).toContain("Next: Quarterly, from 1 Nov 2026");
  });

  it("says what's still due on the next plan, and names it in the payment reminder", () => {
    const f = { ...base, due: 150000, upcoming: [{ ...next, paid_paise: 300000 }] };
    expect(text(f, "next_plan")).toContain("₹1,500 of ₹4,500 is still due.");
    expect(text(f, "payment_due")).toContain("₹1,500 is still due for your Quarterly plan at Iron Temple.");
    expect(text(f, "membership")).not.toContain("Due:");  // the current plan is paid up
  });

  it("lists several booked plans, one to a line", () => {
    const later = { name: "Monthly", starts: "2027-02-01", ends: "2027-02-28", price_paise: 150000, paid_paise: 0 };
    const f = { ...base, due: 150000, upcoming: [next, later] };
    expect(text(f, "next_plan")).toBe([
      "Hi Ravi, your next plans at Iron Temple are booked:", "Quarterly: 1 Nov 2026 to 31 Jan 2027, paid in full",
      "Monthly: 1 Feb 2027 to 28 Feb 2027, ₹1,500 of ₹1,500 due", "The first starts right after your current plan ends, so there's no break.",
    ].join("\n"));
  });

  it("writes a receipt for the latest payment, and what's still due", () => {
    const f = { ...base, due: 50000, lastPayment: { amount_paise: 100000, method: "UPI", on: "2026-10-20T10:00:00Z", plan: "Quarterly" } };
    expect(text(f, "payment_received")).toBe(
      "Hi Ravi, we've received ₹1,000 by UPI on 20 Oct 2026 for your Quarterly plan at Iron Temple. Thank you! ₹500 is still due.");
  });

  it("lists the membership's details, with money only for the desk", () => {
    expect(text(base, "membership")).toBe([
      "Hi Ravi, here are your membership details at Iron Temple.", "Plan: Quarterly", "From 1 Aug 2026 to 31 Oct 2026",
      "Price: ₹4,500", "Paid: ₹4,500", "Member code: M0012",
    ].join("\n"));
    expect(text({ ...base, due: null, sub: null }, "membership")).not.toContain("Price");
  });

  it("misses a member who hasn't come in for a week, but not one who is frozen", () => {
    expect(text({ ...base, lastVisit: "2026-10-15" }, "missed_you")).toBe(
      "Hi Ravi, we haven't seen you at Iron Temple since 15 Oct 2026. Everything okay? Your Quarterly plan runs till 31 Oct 2026, so come in for a workout this week!");
    expect(kinds({ ...base, lastVisit: "2026-10-20" })).not.toContain("missed_you");
    const frozen = { ...base, lastVisit: "2026-10-01", plan: { ...base.plan!, frozen_from: "2026-10-10", frozen_until: "2026-10-30" } };
    expect(kinds(frozen)).toContain("frozen");
    expect(kinds(frozen)).not.toContain("missed_you");
  });

  it("welcomes them with their code, and the app when they have a login", () => {
    expect(text({ ...base, hasLogin: true }, "welcome")).toContain("Your member code is M0012.");
    expect(text({ ...base, hasLogin: true }, "welcome")).toContain("Sign in to the app with this mobile number");
    expect(text({ ...base, plan: null }, "welcome")).toBe("Hi Ravi, welcome to Iron Temple! Your member code is M0012. Check in at the front desk when you come in.");
  });
});

describe("the cards' and rows' own messages", () => {
  it("writes a receipt for any payment, not just the latest", () => {
    const old = { amount_paise: 200000, method: "Cash", on: "2026-08-01T05:00:00Z" };
    expect(receiptChat(base, old).text).toBe("Hi Ravi, we've received ₹2,000 by Cash on 1 Aug 2026 for your membership at Iron Temple. Thank you!");
  });

  it("confirms one booked plan from its row, even when more are booked", () => {
    const later = { name: "Monthly", starts: "2027-02-01", ends: "2027-02-28", price_paise: 150000, paid_paise: 150000 };
    expect(nextPlanChat(base, [later]).text).toBe("Hi Ravi, your next plan at Iron Temple is booked: Monthly, from 1 Feb 2027 to 28 Feb 2027. It's paid in full. Thank you!");
  });

  it("gives the membership card the renewal while it's ending, the freeze while frozen, else the details", () => {
    expect(membershipChat(memberChats(base))?.kind).toBe("renewal");
    const frozen = { ...base, plan: { ...base.plan!, ends: "2026-12-31", frozen_from: "2026-10-10", frozen_until: "2026-10-30" } };
    expect(membershipChat(memberChats(frozen))?.kind).toBe("frozen");
    expect(membershipChat(memberChats({ ...base, plan: { ...base.plan!, ends: "2026-12-31" } }))?.kind).toBe("membership");
    expect(membershipChat(memberChats({ ...base, plan: null }))).toBeUndefined();
  });
});

describe("whatsappLink", () => {
  it("opens a chat with the Indian number and the words typed in", () => {
    expect(whatsappLink("+91 98000 00001")).toBe("https://wa.me/919800000001");
    expect(whatsappLink("9800000001", "Hi Ravi & co\nthanks")).toBe("https://wa.me/919800000001?text=Hi%20Ravi%20%26%20co%0Athanks");
  });
});
