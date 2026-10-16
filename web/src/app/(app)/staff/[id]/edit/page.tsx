"use client";
import { useParams, useRouter } from "next/navigation";

import { useStaffRetrieve } from "@/api/gen/staff/staff";
import { TaskBar } from "@/components/shell";
import { SkeletonRows } from "@/components/ui";
import { StaffForm } from "@/features/staff-form";

export default function EditStaff() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const s = useStaffRetrieve(Number(id)).data?.data;
  const label = s?.role === "receptionist" ? "Receptionist" : "Trainer";
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={`Edit ${label}`} />
      <main className="rl-app__main">
        {s ? <StaffForm roleName={s.role as "trainer" | "receptionist"} staff={s} onSaved={() => router.push(`/staff/${id}`)} /> : <SkeletonRows n={4} />}
      </main>
    </div>
  );
}
