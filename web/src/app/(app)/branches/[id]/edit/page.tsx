"use client";
import { useParams, useRouter } from "next/navigation";

import { useBranchesRetrieve } from "@/api/gen/branches/branches";
import { TaskBar } from "@/components/shell";
import { SkeletonRows } from "@/components/ui";
import { BranchForm } from "@/features/branch-form";

export default function EditBranch() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const b = useBranchesRetrieve(Number(id)).data?.data;
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Edit Branch" />
      <main className="rl-app__main">{b ? <BranchForm branch={b} onSaved={() => router.push("/branches")} /> : <SkeletonRows n={4} />}</main>
    </div>
  );
}
