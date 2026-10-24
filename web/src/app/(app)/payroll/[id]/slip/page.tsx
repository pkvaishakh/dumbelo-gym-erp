"use client";
import { useParams } from "next/navigation";

import { SalarySlip } from "@/features/payroll";

export default function PayrollSlip() {
  const { id } = useParams<{ id: string }>();
  return <SalarySlip id={Number(id)} back={`/payroll/${id}`} />;
}
