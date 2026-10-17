"use client";
import { Printer } from "lucide-react";
import { useParams } from "next/navigation";

import { usePayslipsRetrieve } from "@/api/gen/payslips/payslips";
import { DetailBar } from "@/components/shell";
import { Icon, SkeletonRows } from "@/components/ui";
import { Breakdown } from "@/features/payroll";
import { day, monthLabel, PAY_METHOD, phone, rupees } from "@/lib/format";

const ROLE: Record<string, string> = { admin: "Admin", receptionist: "Receptionist", trainer: "Trainer" };

/** The salary slip to print or save as a PDF from the browser: the same breakdown as the payslip, on plain paper.
 *  The app bar, the button and the tab bar don't print (rl-noprint). */
export default function SalarySlip() {
  const { id } = useParams<{ id: string }>();
  const s = usePayslipsRetrieve(Number(id)).data?.data;
  return (
    <div className="rl-app rl-root">
      <div className="rl-noprint"><DetailBar title="Salary slip" back={`/payroll/${id}`} /></div>
      <main className="rl-app__main">
        {!s ? <SkeletonRows n={6} /> : (
          <>
            <section className="rl-section">
              <div className="rl-card rl-card--pad">
                <p className="rl-row__meta" style={{ margin: 0 }}>{s.gym_name}</p>
                <h2 className="rl-section__title" style={{ margin: "var(--space-1) 0 0" }}>Salary slip, {monthLabel(s.month)}</h2>
                <dl className="rl-facts">
                  <dt>Name</dt><dd>{s.staff_name}</dd>
                  <dt>Role</dt><dd>{ROLE[s.staff_role] ?? s.staff_role}</dd>
                  <dt>Branch</dt><dd>{s.branch_name}</dd>
                  {s.staff_phone && <><dt>Mobile number</dt><dd>{phone(s.staff_phone)}</dd></>}
                  <dt>Status</dt><dd>{s.status === "approved" ? `Approved${s.approved_at ? ` ${day(s.approved_at.slice(0, 10))}` : ""}${s.approved_by_name ? ` by ${s.approved_by_name}` : ""}` : "Draft, not approved yet"}</dd>
                </dl>
              </div>
            </section>
            <Breakdown s={s} />
            <section className="rl-section" aria-label="Payments">
              <div className="rl-card rl-card--pad">
                <h2 className="rl-section__title" style={{ margin: 0 }}>Paid</h2>
                {s.payments.length ? (
                  <dl className="rl-facts">
                    {s.payments.map((p) => <PaidLine key={p.id} label={`${day(p.paid_on)}, ${PAY_METHOD[p.method]}`} value={rupees(p.amount_paise)} />)}
                  </dl>
                ) : <p className="rl-row__meta" style={{ margin: "var(--space-2) 0 0" }}>Nothing paid yet.</p>}
                <p className="rl-total"><span>{s.owed_paise ? "Still to pay" : "Paid in full"}</span><span>{rupees(s.owed_paise || s.paid_paise)}</span></p>
              </div>
            </section>
            <section className="rl-section rl-noprint">
              <button className="rl-button rl-button--block" type="button" onClick={() => window.print()}><Icon as={Printer} size="sm" />Print Salary Slip</button>
              <p className="rl-field__hint">To save it as a PDF, choose Save as PDF in the print window.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function PaidLine({ label, value }: { label: string; value: string }) {
  return <><dt>{label}</dt><dd>{value}</dd></>;
}
