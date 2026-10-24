"use client";
/* The gym's workout plans (More → Workout plans): coach-screens' PlanLibrary. */
import { Suspense } from "react";

import { PlanLibrary } from "@/features/coach-screens";

export default function Page() {
  return <Suspense><PlanLibrary kind="workout" /></Suspense>;
}
