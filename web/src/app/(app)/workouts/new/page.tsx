"use client";
/* New Plan, or ?copy=<id> to copy one: coach-screens' NewPlanScreen. */
import { Suspense } from "react";

import { NewPlanScreen } from "@/features/coach-screens";

export default function Page() {
  return <Suspense><NewPlanScreen kind="workout" /></Suspense>;
}
