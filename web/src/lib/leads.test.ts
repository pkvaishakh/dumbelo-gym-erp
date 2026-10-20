import { describe, expect, it } from "vitest";

import { campaignTags, checkLead, EMPTY_LEAD, mobileDigits } from "./leads";

const full = { name: "Anil Menon", phone: "98470 12345", gym_name: "Pulse Fitness", city: "Kochi", branches: "2-3" as const, email: "" };

describe("mobileDigits", () => {
  it("keeps the ten digits however the number is written", () => {
    expect(mobileDigits("98470 12345")).toBe("9847012345");
    expect(mobileDigits("+91 98470-12345")).toBe("9847012345");
    expect(mobileDigits("919847012345")).toBe("9847012345");
    expect(mobileDigits("12345")).toBe("12345");
  });
});

describe("checkLead", () => {
  it("says what each empty field needs, in the API's words", () => {
    expect(checkLead(EMPTY_LEAD)).toEqual({
      name: "Enter your name", phone: "Enter your mobile number", gym_name: "Enter your gym’s name", city: "Enter your city",
      branches: "Choose how many branches",
    });
  });

  it("passes a complete form, with or without an email", () => {
    expect(checkLead(full)).toEqual({});
    expect(checkLead({ ...full, email: "anil@pulse.in" })).toEqual({});
  });

  it("catches a short number, blank-looking names and a broken email", () => {
    expect(checkLead({ ...full, phone: "98470", name: "   ", email: "anil@" })).toEqual({
      phone: "Enter a 10-digit mobile number", name: "Enter your name", email: "Enter an email like you@gym.com, or leave it empty",
    });
  });
});

describe("campaignTags", () => {
  it("reads the utm tags, and leaves the missing ones empty", () => {
    expect(campaignTags("?utm_source=google&utm_campaign=kerala-gyms&x=1")).toEqual({ utm_source: "google", utm_medium: "", utm_campaign: "kerala-gyms" });
    expect(campaignTags("")).toEqual({ utm_source: "", utm_medium: "", utm_campaign: "" });
    expect(campaignTags(`?utm_source=${"a".repeat(150)}`).utm_source).toHaveLength(100);
  });
});
