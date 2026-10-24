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
  const [done, setDone] = useState<{ staff: Staff; linked: boolean } | null>(null);
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={`Add ${roleName === "trainer" ? "Trainer" : "Receptionist"}`} />
      <main className="rl-app__main"><StaffForm roleName={roleName} onSaved={(staff, linked) => setDone({ staff, linked })} /></main>
      <Sheet open={!!done} onClose={() => {}} closable={false}>
        {done && (
          <>
            <Confirm title={`${done.staff.name} is on the team`}
              text={`They sign in as @${done.staff.username} with ${done.linked ? "their own password, as they do at their other gym" : "the password you set"}.`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/staff/${done.staff.id}`}>View Profile</Link>
              <Link className="rl-button rl-button--secondary rl-button--block" href={`/staff?role=${roleName}`}>Done</Link>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><AddStaff /></Suspense>; }
