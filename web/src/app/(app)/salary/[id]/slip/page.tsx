"use client";
import { useParams } from "next/navigation";

import { SalarySlip } from "@/features/payroll";

export default function MySalarySlip() {
  const { id } = useParams<{ id: string }>();
  return <SalarySlip id={Number(id)} back={`/salary/${id}`} />;
}
