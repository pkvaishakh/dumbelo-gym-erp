"use client";
import { useParams } from "next/navigation";

import { useBillingInvoicesRetrieve } from "@/api/gen/billing/billing";
import { InvoicePaper, PrintFrame } from "@/features/dumbelo-invoices";

/** The Dumbelo invoice to print or save as a PDF. */
export default function PrintInvoice() {
  const { id } = useParams<{ id: string }>();
  const inv = useBillingInvoicesRetrieve(Number(id)).data?.data;
  return (
    <PrintFrame title="Invoice" back={`/dumbelo-plan/invoices/${id}`} label="Print Invoice" ready={!!inv}>
      {inv && <InvoicePaper inv={inv} />}
    </PrintFrame>
  );
}
