/** Shapes of endpoints the OpenAPI schema leaves loose. Keep in step with the views in api/apps. */
import type { PlanKindEnum, PTPlan } from "@/api/gen/model";

export type SessionCounts = { session: string; member: number; trainer: number; receptionist: number; admin: number };

export type Summary = {
  date: string;
  revenue: { today_paise: number; month_paise: number };
  expenses_today_paise: number;
  expenses_month_paise: number;
  members: { total: number; active: number; expiring: number; due: number; frozen: number; expired: number; none: number };
  dues: { members: number; total_paise: number };
  checkins: { total: number; sessions: SessionCounts[] };
  /** Each branch's day; only when the summary covers all branches. */
  branches?: BranchDay[];
  /** What the gym owes now: bills inside their reminder days and approved salaries not paid in full. */
  expense_dues: { count: number; overdue_bills: number; bills: number; salaries: number; total_paise: number };
};

export type BranchDay = { id: number; name: string; revenue_today_paise: number; expenses_today_paise: number; checkins: number; active_members: number };

export type CheckinSummary = {
  totals: { member: number; trainer: number; receptionist: number; admin: number }; sessions: SessionCounts[];
  member_sources: { desk: number; qr: number; device: number };
  /** Only without a branch: each of your branches' member check-ins. */
  branches?: { id: number; name: string; member: number; member_sources: { desk: number; qr: number; device: number } }[];
};

export type TaskCounts = { all: number; open: number; overdue: number; done: number; by_role: { all: number; trainer: number; receptionist: number } };

export type Collection = { date: string; from: string; to: string; total_paise: number; count: number; by_method: Record<string, number> };

export type TrainerMember = {
  id: number; code: string; name: string; phone: string; goal: string; home_branch: string;
  status: string; payment_due: boolean; plan_ends: string | null; pt: PTPlan | null;
};

export type MemberSelf = TrainerMember & {
  plan: { name: string; kind: PlanKindEnum; starts: string; ends: string; frozen_until: string | null } | null;
  balance_paise: number; trainer_name: string | null; joined_on: string;
};

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
