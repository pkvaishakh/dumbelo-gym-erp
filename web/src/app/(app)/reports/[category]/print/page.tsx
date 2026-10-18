"use client";
import { notFound, useParams } from "next/navigation";
import { Suspense } from "react";

import { SkeletonRows } from "@/components/ui";
import { REPORTS } from "@/features/reports/categories";
import { useReportRange } from "@/features/reports/range";
import { isCategory } from "@/lib/reports";

/** A report category on paper: to print, or save as a PDF from the print window. */
function PrintPage() {
  const { category } = useParams<{ category: string }>();
  const r = useReportRange();
  if (!isCategory(category)) notFound();
  const { Report } = REPORTS[category];
  return <Report r={r} print />;
}

export default function Page() {
  return <Suspense fallback={<SkeletonRows n={6} />}><PrintPage /></Suspense>;
}
