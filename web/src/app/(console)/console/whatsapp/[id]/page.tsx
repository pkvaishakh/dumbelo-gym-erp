"use client";
import { AlertCircle, Building2, Clock, FileText, Hash, KeyRound, Link2, Pencil, ScrollText, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import type { WhatsAppTemplate } from "@/api/gen/model";
import { usePlatformWhatsappAccountsRetrieve, usePlatformWhatsappTemplatesListInfinite } from "@/api/gen/platform/platform";
import { DetailBar } from "@/components/shell";
import { AddButton, Details, Empty, ErrorText, Icon, LoadMore, MenuRow, Section, SkeletonRows } from "@/components/ui";
import { ACCOUNTS, accountTitle, Badge, CredentialsSheet, EditAccountSheet, TemplateSheet } from "@/features/console/whatsapp";
import { ago, day } from "@/lib/format";
import { paged, pages, useAction } from "@/lib/hooks";

/** One WhatsApp number: whether it works (Test Connection), where Meta sends its updates, its credentials (the
 *  last 4 characters only) and its templates. */
export default function WhatsAppAccountScreen() {
  const { id } = useParams<{ id: string }>();
  const q = usePlatformWhatsappAccountsRetrieve(Number(id));
  const account = q.data?.data;
  const templates = usePlatformWhatsappTemplatesListInfinite({ account: Number(id) }, { query: paged });
  const { rows } = pages(templates);
  const [sheet, setSheet] = useState<"edit" | "credentials" | "template" | null>(null);
  const [template, setTemplate] = useState<WhatsAppTemplate | null>(null);
  const test = useAction();
  const bar = (
    <DetailBar title="WhatsApp number" back="/console/whatsapp" action={account && (
      <button className="rl-iconbtn rl-iconbtn--plain" type="button" aria-label="Edit details" aria-haspopup="dialog" onClick={() => setSheet("edit")}><Icon as={Pencil} /></button>
    )} />
  );
  if (q.isError) {
    return (
      <div className="rl-app rl-root">{bar}<main className="rl-app__main">
        <Empty icon={AlertCircle} title="Can't open this number" text={q.error instanceof Error ? q.error.message : "Check your connection and try again."}>
          <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => q.refetch()}>Try Again</button>
        </Empty>
      </main></div>
    );
  }
  if (!account) return <div className="rl-app rl-root">{bar}<main className="rl-app__main"><SkeletonRows n={4} /></main></div>;

  async function runTest() {
    try { await test.run(`${ACCOUNTS}${account!.id}/test/`, undefined, { refresh: [ACCOUNTS] }); } catch { /* shown */ }
  }
  const openTemplate = (t: WhatsAppTemplate | null) => { setTemplate(t); setSheet("template"); };

  return (
    <div className="rl-app rl-root">
      {bar}
      <main className="rl-app__main">
        <div className="rl-identity">
          <div className="rl-identity__text"><h2 className="rl-identity__name">{account.display_number}</h2>
            <p className="rl-identity__meta" style={{ margin: 0 }}><span>{account.verified_name || accountTitle(account)}</span><Badge of="account" status={account.status} /></p></div>
        </div>
        <Section title="Connection">
          <div className="rl-card rl-card--pad">
            <p className="rl-row__title" style={{ margin: 0 }}>
              {account.status === "working" ? "Meta knows this number and took its token" : account.status === "failing" ? "Meta turned it down" : "Not checked with Meta yet"}
            </p>
            <p className="rl-row__meta">
              {account.status === "failing" && account.last_error ? `${account.last_error}. ` : ""}
              {account.checked_at ? `Last checked ${ago(account.checked_at)}.` : "Test Connection asks Meta for the number's details. It sends no message."}
            </p>
            {/* The one accent action: whether the number works is what this screen is for. */}
            <button className="rl-button rl-button--accent rl-button--block" type="button" disabled={test.busy} onClick={runTest}>{test.busy ? "Asking Meta…" : "Test Connection"}</button>
            <ErrorText>{test.error?.message}</ErrorText>
          </div>
        </Section>
        <Section label="WhatsApp log">
          <ul className="rl-card rl-remind">
            <MenuRow icon={ScrollText} title="WhatsApp log" value="What this number sent" href={`/console/messages?account=${account.id}`} />
          </ul>
        </Section>
        <Section title="Details">
          <Details rows={[
            { icon: Building2, label: "Belongs to", value: account.is_shared ? "Rackline: the shared number" : account.gym ? <Link href={`/console/gyms/${account.gym}`}>{account.gym_name}</Link> : null },
            { icon: Hash, label: "Phone number id", value: account.phone_number_id },
            { icon: Hash, label: "WhatsApp Business account id", value: account.waba_id },
            { icon: Clock, label: "Added", value: day(account.created_at) },
          ]} />
        </Section>
        <Section title="Webhook" aside={<p className="rl-section__aside">Meta&apos;s settings</p>}>
          <Details rows={[
            { icon: Link2, label: "Callback URL", value: <span style={{ wordBreak: "break-all" }}>{account.webhook_url}</span> },
            { icon: ShieldCheck, label: "Verify token", value: <span style={{ wordBreak: "break-all" }}>{account.verify_token}</span> },
          ]} />
          <p className="rl-row__meta">Paste both into the Meta app&apos;s WhatsApp webhook settings and subscribe to messages, so delivery updates reach Rackline.</p>
        </Section>
        <Section title="Credentials">
          <Details rows={[
            { icon: KeyRound, label: "Access token", value: `Ends in ${account.access_token_last4}` },
            { icon: KeyRound, label: "App secret", value: `Ends in ${account.app_secret_last4}` },
          ]} />
          <button className="rl-button rl-button--secondary rl-button--block" type="button" aria-haspopup="dialog" style={{ marginTop: "var(--space-3)" }} onClick={() => setSheet("credentials")}>Replace Credentials</button>
        </Section>
        <Section title="Templates" aside={<AddButton label="Add Template" onClick={() => openTemplate(null)} />}>
          {templates.isLoading ? <SkeletonRows n={3} /> : rows.length ? (
            <>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {rows.map((t) => (
                  <li key={t.id}><button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => openTemplate(t)}>
                    <span className="rl-chipicon" aria-hidden="true"><Icon as={FileText} size="sm" /></span>
                    <span className="rl-row__title rl-mrow__name">{t.kind_label}</span>
                    <span className="rl-row__meta rl-mrow__meta">{t.name} • {t.language}</span>
                    <Badge of="template" status={t.status} />
                  </button></li>
                ))}
              </ul>
              <LoadMore q={templates} />
            </>
          ) : (
            <Empty icon={FileText} title="No templates yet" text="Meta sends only approved templates. Add each one Meta has approved for this number, with the details it takes." />
          )}
        </Section>
      </main>
      <EditAccountSheet account={account} open={sheet === "edit"} onClose={() => setSheet(null)} />
      <CredentialsSheet account={account} open={sheet === "credentials"} onClose={() => setSheet(null)} />
      <TemplateSheet accountId={account.id} template={template} open={sheet === "template"} onClose={() => setSheet(null)} />
    </div>
  );
}

