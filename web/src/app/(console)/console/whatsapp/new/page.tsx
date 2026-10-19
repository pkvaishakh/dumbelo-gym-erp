"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { WhatsAppAccount } from "@/api/gen/model";
import { usePlatformGymsRetrieve } from "@/api/gen/platform/platform";
import { TaskBar } from "@/components/shell";
import { Confirm, ErrorText, Sheet } from "@/components/ui";
import { ACCOUNTS, SecretField, type Where, WhereFields, whereErrors } from "@/features/console/whatsapp";
import { ActionBar } from "@/features/sell";
import { fieldError, useAction } from "@/lib/hooks";

/** Add Account: Dumbelo's shared number, or with `?gym=` that gym's own. Nothing is asked of Meta until Test
 *  Connection, on the number's screen. */
function AddAccount() {
  const router = useRouter();
  const gymId = Number(useSearchParams().get("gym")) || null;
  const gym = usePlatformGymsRetrieve(gymId ?? 0, { query: { enabled: !!gymId } }).data?.data;
  const back = gymId ? `/console/gyms/${gymId}` : "/console/whatsapp";
  const [f, setF] = useState<Where>({ waba_id: "", phone_number_id: "", display_number: "" });
  const [secrets, setSecrets] = useState({ access_token: "", app_secret: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [made, setMade] = useState<WhatsAppAccount | null>(null);
  const a = useAction();
  const err = (k: string) => errs[k] ?? fieldError(a.error, k);

  async function save() {
    const e = whereErrors(f);
    if (secrets.access_token.trim().length < 20) e.access_token = "Paste the number's permanent access token from Meta";
    if (secrets.app_secret.trim().length < 16) e.app_secret = "Paste the Meta app's secret (App settings → Basic)";
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = {
      gym: gymId, waba_id: f.waba_id.trim(), phone_number_id: f.phone_number_id.trim(), display_number: f.display_number.trim(),
      access_token: secrets.access_token.trim(), app_secret: secrets.app_secret.trim(),
    };
    try {
      const out = await a.run<WhatsAppAccount>(ACCOUNTS, body, { refresh: [ACCOUNTS] });
      setSecrets({ access_token: "", app_secret: "" }); // nothing to keep in the page once they're saved
      setMade(out!);
    } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={gymId ? "Add WhatsApp Number" : "Add Shared Number"} aside={gymId ? gym?.name : "Dumbelo's own"} onClose={() => router.push(back)} />
      <main className="rl-app__main">
        <p className="rl-row__meta">
          {gymId
            ? `${gym?.name ?? "The gym"}'s own WhatsApp Business account, from its Meta Business settings. It pays Meta for its messages itself.`
            : "The number gyms on Dumbelo's number send from. Their messages are billed on their Dumbelo plan."}
        </p>
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <WhereFields f={f} set={setF} err={err} />
          <fieldset className="rl-fieldset"><legend>Credentials</legend>
            <div className="rl-form">
              <SecretField label="Access token" value={secrets.access_token} onChange={(access_token) => setSecrets({ ...secrets, access_token })}
                error={err("access_token")} hint="A system user's permanent token, with WhatsApp messaging allowed." />
              <SecretField label="App secret" value={secrets.app_secret} onChange={(app_secret) => setSecrets({ ...secrets, app_secret })}
                error={err("app_secret")} hint="Checks that delivery updates really come from Meta." />
              <p className="rl-row__meta">Kept encrypted and never shown again, only their last 4 characters. You can replace them later.</p>
            </div>
          </fieldset>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label="Add Number" busy={a.busy} busyLabel="Adding…" onClick={save} />
      <Sheet open={!!made} onClose={() => router.push(back)} closable={false}>
        {made && (
          <>
            <Confirm title={`${made.display_number} is added`} text="Open it to run Test Connection, set up Meta's webhook and add its templates." />
            <div className="rl-sheet__actions">
              <button className="rl-button rl-button--block" type="button" onClick={() => router.push(`/console/whatsapp/${made.id}`)}>Open Number</button>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => router.push(back)}>Done</button>
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}

export default function Page() { return <Suspense><AddAccount /></Suspense>; }
