"use client";
/* The gym's diet plans (More → Diet plans): coach-screens' PlanLibrary. */
import { Suspense } from "react";

import { PlanLibrary } from "@/features/coach-screens";

export default function Page() {
  return <Suspense><PlanLibrary kind="diet" /></Suspense>;
}
