import { describe, expect, it } from "vitest";

import { whatsappNumber } from "./site";

describe("whatsappNumber", () => {
  it("gives WhatsApp the number with its country code and nothing else", () => {
    expect(whatsappNumber("+91 98765 43210")).toBe("919876543210");
    expect(whatsappNumber("919876543210")).toBe("919876543210");
    expect(whatsappNumber("98765-43210")).toBe("919876543210"); // a bare Indian number
    expect(whatsappNumber("+44 20 7946 0958")).toBe("442079460958");
    expect(whatsappNumber("")).toBe("");
  });
});
