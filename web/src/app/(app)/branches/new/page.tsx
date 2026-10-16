"use client";
import { useRouter } from "next/navigation";

import { TaskBar } from "@/components/shell";
import { BranchForm } from "@/features/branch-form";

export default function AddBranch() {
  const router = useRouter();
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Add Branch" />
      <main className="rl-app__main"><BranchForm onSaved={() => router.push("/branches")} /></main>
    </div>
  );
}
