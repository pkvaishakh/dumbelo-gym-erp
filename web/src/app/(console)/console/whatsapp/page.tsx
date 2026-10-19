"use client";
import { AlertCircle, MessageCircle } from "lucide-react";
import Link from "next/link";

import { usePlatformWhatsappAccountsListInfinite } from "@/api/gen/platform/platform";
import { PageBar } from "@/components/shell";
import { AddButton, Empty, Icon, LoadMore, Section, SkeletonRows } from "@/components/ui";
import { Badge } from "@/features/console/whatsapp";
import { plural } from "@/lib/format";
import { paged, pages } from "@/lib/hooks";

/** The WhatsApp numbers Dumbelo sends from: its shared number first, then gyms' own. A gym's own number is added
 *  from that gym's screen, so there's never a gym to pick here. */
export default function WhatsAppAccounts() {
  const list = usePlatformWhatsappAccountsListInfinite(undefined, { query: paged });
  const { rows } = pages(list);
  const hasShared = rows.some((r) => r.is_shared);
  return (
    <div className="rl-app rl-root">
      <PageBar title="WhatsApp" sub="Numbers and templates" back="/console/more"
        action={!list.isLoading && !hasShared ? <AddButton href="/console/whatsapp/new" label="Add Shared Number" /> : undefined} />
      <main className="rl-app__main">
        <Section label="Numbers">
          {list.isLoading ? <SkeletonRows n={3} /> : list.isError ? (
            <Empty icon={AlertCircle} title="Can't load the numbers" text={list.error instanceof Error ? list.error.message : "Check your connection and try again."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => list.refetch()}>Try Again</button>
            </Empty>
          ) : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((r) => (
                  <li key={r.id}><Link className="rl-mrow" href={`/console/whatsapp/${r.id}`}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={MessageCircle} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{r.display_number}</span>
                    <span className="rl-row__meta rl-mrow__meta">{r.is_shared ? "Shared" : r.gym_name} • {plural(r.template_count, "template")}</span>
                    <Badge of="account" status={r.status} />
                  </Link></li>
                ))}
              </ul>
              <LoadMore q={list} />
            </>
          ) : (
            <Empty icon={MessageCircle} title="No numbers yet" text="Add Dumbelo's shared number first: gyms on Dumbelo's number send their reminders from it.">
              <Link className="rl-button rl-button--block" href="/console/whatsapp/new">Add Shared Number</Link>
            </Empty>
          )}
        </Section>
        <p className="rl-row__meta">To add a gym&apos;s own number, open the gym from Gyms. Which number a gym sends from is set on its Dumbelo plan.</p>
      </main>
    </div>
  );
}
