"use client";
import { useParams } from "next/navigation";

import { useAccountsRetrieve } from "@/api/gen/accounts/accounts";
import { TaskBar } from "@/components/shell";
import { SkeletonRows } from "@/components/ui";
import { AccountForm } from "@/features/account-form";

export default function EditAccount() {
  const { id } = useParams<{ id: string }>();
  const account = useAccountsRetrieve(Number(id)).data?.data;
  if (!account) return <div className="rl-app rl-app--task rl-root"><TaskBar title="Edit Account" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  return <AccountForm account={account} />;
}
