"use client";
/* The frame of a member's own My plans and My payments: the title, what they owe, and a word for staff who land here. */
import { Ticket } from "lucide-react";

import { useMembersList } from "@/api/gen/members/members";
import { PageBar } from "@/components/shell";
import { Empty, Section } from "@/components/ui";
import { rupees } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { MemberSelf } from "@/lib/types";

/** `children` gets the member (undefined while it loads); `what` names the screen for staff ("plans"). */
export function MemberScreen({ title, what, children }: { title: string; what: string; children: (me?: MemberSelf) => React.ReactNode }) {
  const { role } = useSession();
  const member = role.role === "member";
  const me = useMembersList(undefined, { query: { enabled: member } }).data?.data.results?.[0] as unknown as MemberSelf | undefined;
  return (
    <div className="rl-app rl-root">
      <PageBar title={title} back />
      <main className="rl-app__main">
        {!member ? (
          <Empty icon={Ticket} title="For members" text={`Members see their own ${what} here.`} />
        ) : (
          <>
            {me && me.balance_paise > 0 && (
              <Section label="Payment due">
                <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}><strong>{rupees(me.balance_paise)} is due.</strong> Pay at the front desk.</p></div>
              </Section>
            )}
            {children(me)}
          </>
        )}
      </main>
    </div>
  );
}
