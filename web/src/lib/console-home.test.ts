import { describe, expect, it } from "vitest";

import type { PlatformSummary } from "@/api/gen/model";

import { andList, consoleAttention, serverMeta } from "./console-home";

const quiet: PlatformSummary = {
  checked_at: "2026-10-19T14:00:00+05:30",
  gyms: { active: 12, trial: 3, suspended: 1, new_this_month: 2 },
  money: { owed_paise: 0, gyms_owing: 0, overdue_paise: 0, overdue_invoices: 0, gyms_overdue: 0 },
  branch_requests: { waiting: 0 },
  whatsapp: { delivered_today: 140, failed_today: 0, waiting_retry: 0, shared_messages: 2300, shared_paise: 34500 },
  server: { down: [], failed_jobs: [] },
};

describe("andList", () => {
  it("joins names the way people say them", () => {
    expect(andList([])).toBe("");
    expect(andList(["Worker"])).toBe("Worker");
    expect(andList(["Worker", "Beat"])).toBe("Worker and Beat");
    expect(andList(["Database", "Redis", "Worker"])).toBe("Database, Redis and Worker");
  });
});

describe("consoleAttention", () => {
  it("is all zeros when nothing needs you, so the card shows its quiet line", () => {
    expect(consoleAttention(quiet).map((r) => r.count)).toEqual([0, 0, 0, 0]);
  });

  it("puts the server first and says what is down and what failed", () => {
    const s: PlatformSummary = {
      ...quiet,
      money: { owed_paise: 570000, gyms_owing: 2, overdue_paise: 390000, overdue_invoices: 3, gyms_overdue: 2 },
      branch_requests: { waiting: 1 },
      whatsapp: { ...quiet.whatsapp, failed_today: 4 },
      server: {
        down: [
          { key: "worker", label: "Worker", state: "down", detail: "No answer in 2 seconds", at: null },
          { key: "beat", label: "Beat", state: "down", detail: "Late", at: "2026-10-19T13:40:00+05:30" },
        ],
        failed_jobs: [{ job: "reminders", label: "Reminders", finished_at: "2026-10-19T13:00:00+05:30", error: "Meta didn't answer" }],
      },
    };
    const rows = consoleAttention(s);
    expect(rows.map((r) => [r.count, r.title, r.meta, r.href])).toEqual([
      [3, "Server problems", "Worker and Beat down • Reminders failed", "/console/server"],
      [3, "Overdue invoices", "₹3,900 from 2 gyms", "/console/gyms?owes=overdue"],
      [1, "Branch requests", "Gyms waiting for your answer", "/console/requests"],
      [4, "WhatsApp messages failed", "Today, on every number", "/console/messages?status=failed"],
    ]);
    expect(serverMeta({ down: [], failed_jobs: s.server.failed_jobs })).toBe("Reminders failed");
  });
});
