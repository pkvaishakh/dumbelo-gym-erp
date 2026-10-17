"use client";
import { useParams } from "next/navigation";

import { useRecurringExpensesRetrieve } from "@/api/gen/recurring-expenses/recurring-expenses";
import { TaskBar } from "@/components/shell";
import { SkeletonRows } from "@/components/ui";
import { RecurringForm } from "@/features/recurring-form";

export default function EditRecurringExpense() {
  const { id } = useParams<{ id: string }>();
  const rule = useRecurringExpensesRetrieve(Number(id)).data?.data;
  if (!rule) return <div className="rl-app rl-app--task rl-root"><TaskBar title="Edit Recurring Expense" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  return <RecurringForm rule={rule} />;
}
