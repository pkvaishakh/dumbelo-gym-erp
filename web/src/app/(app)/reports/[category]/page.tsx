"use client";
import { notFound, useParams } from "next/navigation";
import { Suspense } from "react";

import { SkeletonRows } from "@/components/ui";
import { REPORTS } from "@/features/reports/categories";
import { useReportRange } from "@/features/reports/range";
import { isCategory } from "@/lib/reports";

/** One report category: its own figures for the period and branch in the URL, with Download in the app bar. */
function CategoryPage() {
  const { category } = useParams<{ category: string }>();
  const r = useReportRange();
  if (!isCategory(category)) notFound();
  const { Report } = REPORTS[category];
  return <Report r={r} />;
}

export default function Page() {
  return <Suspense fallback={<SkeletonRows n={6} />}><CategoryPage /></Suspense>;
}
