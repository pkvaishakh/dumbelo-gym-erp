"use client";
/* Each report category's screen and icon, for the Reports list and the /reports/[category] routes. */
import { CalendarCheck, ClipboardCheck, IndianRupee, Landmark, Receipt, Users, type LucideIcon } from "lucide-react";

import type { Category } from "@/lib/reports";

import { AttendanceReport } from "./attendance";
import { ExpensesReport } from "./expenses";
import { MembersReport } from "./members";
import { MoneyReport } from "./money";
import type { ReportRange } from "./range";
import { RevenueReport } from "./revenue";
import { TasksReport } from "./tasks";

export const REPORTS: Record<Category, { icon: LucideIcon; Report: (p: { r: ReportRange; print?: boolean }) => React.ReactNode }> = {
  revenue: { icon: IndianRupee, Report: RevenueReport },
  expenses: { icon: Receipt, Report: ExpensesReport },
  money: { icon: Landmark, Report: MoneyReport },
  members: { icon: Users, Report: MembersReport },
  attendance: { icon: CalendarCheck, Report: AttendanceReport },
  tasks: { icon: ClipboardCheck, Report: TasksReport },
};
