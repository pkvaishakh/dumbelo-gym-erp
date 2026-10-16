"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { Staff } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Confirm, Sheet } from "@/components/ui";
import { StaffForm } from "@/features/staff-form";

function AddStaff() {
  const roleName = useSearchParams().get("role") === "receptionist" ? "receptionist" : "trainer";
  const [done, setDone] = useState<Staff | null>(null);
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={`Add ${roleName === "trainer" ? "Trainer" : "Receptionist"}`} />
      <main className="rl-app__main"><StaffForm roleName={roleName} onSaved={setDone} /></main>
      <Sheet open={!!done} onClose={() => {}} closable={false}>
        {done && (
          <>
            <Confirm title={`${done.name} is on the team`} text={`They sign in with ${done.email} and the password you set.`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/staff/${done.id}`}>View Profile</Link>
              <Link className="rl-button rl-button--secondary rl-button--block" href={`/staff?role=${roleName}`}>Done</Link>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><AddStaff /></Suspense>; }
