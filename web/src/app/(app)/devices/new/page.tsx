"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { DeviceWithToken } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { ErrorText, Field } from "@/components/ui";
import { TokenSheet } from "@/features/devices";
import { ActionBar } from "@/features/sell";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

/** Add Device: name it, type the serial off the box, pick the door it stands at. The token comes back once. */
export default function AddDevice() {
  const router = useRouter();
  const { role } = useSession();
  const blank = { name: "", serial: "", branch: role.branches[0]?.id ?? 0 };
  const [f, setF] = useState(blank);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [added, setAdded] = useState<DeviceWithToken | null>(null);
  const a = useAction();

  async function save() {
    const e: Record<string, string> = {};
    if (!f.name.trim()) e.name = "Give the device a name";
    if (!f.serial.trim()) e.serial = "Type the serial number printed on the device";
    if (!f.branch) e.branch = "Choose the branch it stands at";
    setErrs(e);
    if (Object.keys(e).length) return;
    try {
      const d = await a.run<DeviceWithToken>("/api/devices/", { ...f, name: f.name.trim(), serial: f.serial.trim() }, { refresh: ["/api/devices/"] });
      setAdded(d!);
    } catch { /* shown */ }
  }
  const err = (k: string) => errs[k] ?? fieldError(a.error, k);

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Add Device" />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Device name" error={err("name")} hint="How you tell your devices apart.">
            {(id, describedBy) => (
              <input className="rl-field__input" id={id} aria-describedby={describedBy} value={f.name} placeholder="Front turnstile"
                autoCapitalize="words" enterKeyHint="next" onChange={(e) => setF({ ...f, name: e.target.value })} />
            )}
          </Field>
          <Field label="Serial number" error={err("serial")} hint="Printed on the device or its box.">
            {(id, describedBy) => (
              <input className="rl-field__input" id={id} aria-describedby={describedBy} value={f.serial} placeholder="ZK-10234"
                autoCapitalize="characters" autoCorrect="off" spellCheck={false} enterKeyHint="next" onChange={(e) => setF({ ...f, serial: e.target.value })} />
            )}
          </Field>
          <fieldset className="rl-fieldset"><legend>Branch</legend>
            <div className="rl-chips">
              {role.branches.map((b) => (
                <label className="rl-chipopt" key={b.id}>
                  <input type="radio" name="branch" checked={f.branch === b.id} onChange={() => setF({ ...f, branch: b.id })} />
                  <span>{b.name}</span>
                </label>
              ))}
            </div>
            <ErrorText>{err("branch")}</ErrorText>
          </fieldset>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label="Add Device" busy={a.busy} busyLabel="Adding…" onClick={save} />
      <TokenSheet open={!!added} name={added?.name ?? ""} token={added?.token ?? ""} onClose={() => router.push("/devices")}>
        <button className="rl-button rl-button--block" type="button" onClick={() => router.push("/devices")}>Done</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => { setAdded(null); setF(blank); }}>Add Another</button>
      </TokenSheet>
    </div>
  );
}
