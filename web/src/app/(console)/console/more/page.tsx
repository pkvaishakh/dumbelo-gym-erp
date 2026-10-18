"use client";
import { Building2, KeyRound, LogOut, Mail, Pencil, UserRound } from "lucide-react";
import { useState } from "react";

import { PageBar } from "@/components/shell";
import { Details, Icon, MenuRow, Section } from "@/components/ui";
import { AccountSheet, PasswordSheet } from "@/features/account";
import { gymSlug } from "@/lib/api";
import { phone } from "@/lib/format";
import { useWho } from "@/lib/session";

/** The Rackline admin's own account, and the gyms they also work at (opening one leaves the Console). */
export default function ConsoleMore() {
  const { me, signOut } = useWho();
  const [sheet, setSheet] = useState<"details" | "password" | null>(null);
  const open = (slug: string) => { gymSlug.set(slug); window.location.assign("/home"); };
  return (
    <div className="rl-app rl-root">
      <PageBar title="More" sub={`${me.name} • Rackline admin`} />
      <main className="rl-app__main">
        {me.roles.length > 0 && (
          <Section title="Your gyms">
            <ul className="rl-card rl-remind">
              {me.roles.map((r) => <MenuRow key={r.gym} icon={Building2} title={`Open ${r.gym_name}`} onClick={() => open(r.gym)} />)}
            </ul>
          </Section>
        )}
        <Section title="Account Details">
          <Details rows={[
            { icon: UserRound, label: "Name", value: me.name },
            { icon: Mail, label: "Email", value: me.email },
            { icon: UserRound, label: "Mobile number", value: phone(me.phone) },
          ]} />
          <ul className="rl-card rl-remind" style={{ marginTop: "var(--space-3)" }}>
            <MenuRow icon={Pencil} title="Edit Details" onClick={() => setSheet("details")} />
            <MenuRow icon={KeyRound} title="Change Password" onClick={() => setSheet("password")} />
          </ul>
        </Section>
        <Section label="Sign out">
          <ul className="rl-card rl-remind">
            <li><button className="rl-remind__row" type="button" onClick={signOut}>
              <span className="rl-chipicon" aria-hidden="true"><Icon as={LogOut} size="sm" /></span>
              <span className="rl-remind__text"><span className="rl-row__title">Sign Out</span></span>
            </button></li>
          </ul>
        </Section>
      </main>
      <AccountSheet open={sheet === "details"} onClose={() => setSheet(null)} />
      <PasswordSheet open={sheet === "password"} onClose={() => setSheet(null)} />
    </div>
  );
}
