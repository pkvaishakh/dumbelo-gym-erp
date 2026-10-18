"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { AccountForm } from "@/features/account-form";

function AddAccount() {
  const p = useSearchParams();
  const branch = Number(p.get("branch")) || undefined;
  return <AccountForm kind={p.get("kind") === "cash" ? "cash" : "bank"} branch={branch} />;
}

export default function Page() { return <Suspense><AddAccount /></Suspense>; }
