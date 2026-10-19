"use client";
import { SearchX } from "lucide-react";
import { useParams } from "next/navigation";

import { useBillingInvoicesRetrieve } from "@/api/gen/billing/billing";
import { Empty } from "@/components/ui";
import { PrintFrame, ReceiptPaper } from "@/features/dumbelo-invoices";

/** A payment's receipt from Dumbelo, to print or save as a PDF. */
export default function PrintReceipt() {
  const { id, pid } = useParams<{ id: string; pid: string }>();
  const q = useBillingInvoicesRetrieve(Number(id));
  const inv = q.data?.data;
  const p = inv?.payments.find((x) => x.id === Number(pid));
  return (
    <PrintFrame title="Receipt" back={`/dumbelo-plan/invoices/${id}`} label="Print Receipt" ready={!!inv}>
      {inv && (p ? <ReceiptPaper inv={inv} p={p} /> : <Empty icon={SearchX} title="No such receipt" text="It isn't on this invoice. Go back and pick a payment." />)}
    </PrintFrame>
  );
}
