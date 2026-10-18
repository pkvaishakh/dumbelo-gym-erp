"use client";
import { AlertCircle, BadgeIndianRupee, Building2, CalendarDays, Clock, FileText, Mail, MessageCircle, Pencil, UserRound } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { usePlatformGymsPlanRetrieve, usePlatformGymsRetrieve, usePlatformWhatsappAccountsList } from "@/api/gen/platform/platform";
import { DetailBar } from "@/components/shell";
import { Details, Empty, Icon, MenuRow, Photo, Section, SkeletonRows, Status } from "@/components/ui";
import { AdminsSection } from "@/features/console/admins";
import { EditGymSheet, StatusSheet } from "@/features/console/gym-sheets";
import { GymMessages } from "@/features/console/messages";
import { GymStatus } from "@/features/console/parts";
import { branchesOf, day, GYM_STATUS, plural, rupees, WHATSAPP_STATUS } from "@/lib/format";

/** One gym, as Rackline sees it: status, branches, its Rackline plan, when its messages go out and its admins. Never
 *  what is inside it (members, money, visits). */
export default function GymScreen() {
  const { id } = useParams<{ id: string }>();
  const q = usePlatformGymsRetrieve(Number(id));
  const g = q.data?.data;
  const plan = usePlatformGymsPlanRetrieve(Number(id)).data?.data;
  const whatsapp = usePlatformWhatsappAccountsList({ gym: Number(id) }).data?.data.results[0]; // at most one a gym
  const [editing, setEditing] = useState(false);
  const [change, setChange] = useState<"suspend" | "activate" | null>(null);
  if (q.isError) {
    return (
      <div className="rl-app rl-root"><DetailBar title="Gym" back="/console" /><main className="rl-app__main">
        <Empty icon={AlertCircle} title="Can't open this gym" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      </main></div>
    );
  }
  if (!g) return <div className="rl-app rl-root"><DetailBar title="Gym" back="/console" /><main className="rl-app__main"><SkeletonRows n={4} /></main></div>;
  const suspended = g.status === "suspended";
  return (
    <div className="rl-app rl-root">
      <DetailBar title="Gym" back="/console" action={<button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Edit gym" aria-haspopup="dialog" onClick={() => setEditing(true)}><Icon as={Pencil} /></button>} />
      <main className="rl-app__main">
        <div className="rl-identity">
          <Photo name={g.name} size="xl" />
          <div className="rl-identity__text"><h2 className="rl-identity__name">{g.name}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{g.slug}</span><GymStatus status={g.status} /></p></div>
        </div>
        <Section title="Details">
          <Details rows={[
            { icon: UserRound, label: "Owner", value: g.owner_name ?? "No owner" },
            { icon: Mail, label: "Billing email", value: g.billing_email },
            { icon: Clock, label: "Time zone", value: g.timezone.replace(/_/g, " ") },
            { icon: CalendarDays, label: "On Rackline since", value: day(g.created_at) },
            ...(g.status_changed_at ? [{
              icon: AlertCircle, label: `${GYM_STATUS[g.status]?.label ?? g.status} since ${day(g.status_changed_at)}`, value: g.status_reason || "No reason given",
            }] : []),
          ]} />
        </Section>
        <Section title="Branches" aside={<span className="rl-row__meta">{plural(g.branch_count, "active branch", "active branches")}</span>}>
          {g.branches.length ? (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {g.branches.map((b) => (
                <li key={b.id}><div className="rl-mrow">
                  <span className="rl-chipicon" aria-hidden="true"><Icon as={Building2} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{b.name}</span>
                  <span className="rl-row__meta rl-mrow__meta">{plural(b.member_count, "member")}</span>
                  {!b.is_active && <Status status="off" />}
                </div></li>
              ))}
            </ul>
          ) : <div className="rl-card rl-card--pad"><p className="rl-row__meta" style={{ margin: 0 }}>No branches yet.</p></div>}
        </Section>
        <Section title="Rackline plan">
          <ul className="rl-card rl-remind">
            <MenuRow icon={BadgeIndianRupee} title={plan ? `${rupees(plan.monthly_paise)} a month` : "Rackline plan"} href={`/console/gyms/${g.id}/plan`}
              value={plan ? branchesOf(plan.branches_in_use, plan.branch_quota) : undefined} />
            <MenuRow icon={FileText} title="Invoices and payments" href={`/console/gyms/${g.id}/invoices`}
              value={g.owed_paise ? `${rupees(g.owed_paise)} owed` : "Nothing owed"} />
            {/* Its own number, or the way to add one. Which number it sends from is on its Rackline plan. */}
            <MenuRow icon={MessageCircle} title="WhatsApp" href={whatsapp ? `/console/whatsapp/${whatsapp.id}` : `/console/whatsapp/new?gym=${g.id}`}
              value={whatsapp ? `${whatsapp.display_number} • ${WHATSAPP_STATUS[whatsapp.status]?.label ?? whatsapp.status}` : "Add Own Number"} />
          </ul>
        </Section>
        <GymMessages gymId={g.id} />
        <AdminsSection gymId={g.id} />
        <Section label="Account">
          {suspended || g.status === "trial" ? (
            <button className="rl-button rl-button--block rl-button--secondary" type="button" aria-haspopup="dialog" onClick={() => setChange("activate")}>Activate Gym</button>
          ) : null}
          {!suspended && (
            <button className="rl-button rl-button--block rl-button--danger-quiet" type="button" aria-haspopup="dialog" style={g.status === "trial" ? { marginTop: "var(--space-3)" } : undefined} onClick={() => setChange("suspend")}>Suspend Gym</button>
          )}
        </Section>
      </main>
      <EditGymSheet gym={g} open={editing} onClose={() => setEditing(false)} />
      <StatusSheet gym={g} change={change} onClose={() => setChange(null)} />
    </div>
  );
}
