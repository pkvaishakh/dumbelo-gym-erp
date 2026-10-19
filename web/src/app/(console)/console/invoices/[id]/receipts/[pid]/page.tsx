"use client";
import { SearchX } from "lucide-react";
import { useParams } from "next/navigation";

import { usePlatformInvoicesRetrieve } from "@/api/gen/platform/platform";
import { Empty } from "@/components/ui";
import { PrintFrame, ReceiptPaper } from "@/features/dumbelo-invoices";

/** A payment's receipt to print or save as a PDF, from the Console. The same paper the gym's admins print. */
export default function ConsolePrintReceipt() {
  const { id, pid } = useParams<{ id: string; pid: string }>();
  const inv = usePlatformInvoicesRetrieve(Number(id)).data?.data;
  const p = inv?.payments.find((x) => x.id === Number(pid));
  return (
    <PrintFrame title="Receipt" back={`/console/invoices/${id}`} label="Print Receipt" ready={!!inv}>
      {inv && (p ? <ReceiptPaper inv={inv} p={p} /> : <Empty icon={SearchX} title="No such receipt" text="It isn't on this invoice. Go back and pick a payment." />)}
    </PrintFrame>
  );
}
