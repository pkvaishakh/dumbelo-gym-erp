"use client";
import { useParams } from "next/navigation";

import { usePlatformInvoicesRetrieve } from "@/api/gen/platform/platform";
import { InvoicePaper, PrintFrame } from "@/features/rackline-invoices";

/** A gym's Rackline invoice to print or save as a PDF, from the Console. The same paper its admins print. */
export default function ConsolePrintInvoice() {
  const { id } = useParams<{ id: string }>();
  const inv = usePlatformInvoicesRetrieve(Number(id)).data?.data;
  return (
    <PrintFrame title="Invoice" back={`/console/invoices/${id}`} label="Print Invoice" ready={!!inv}>
      {inv && <InvoicePaper inv={inv} />}
    </PrintFrame>
  );
}
