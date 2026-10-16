"use client";
/* The sheets behind the Devices screen: what a device is, renaming it, a new token, switching it off. */
import { Building2, Check, Copy, Clock, Hash, Power } from "lucide-react";
import { useEffect, useState } from "react";

import type { Device, DeviceWithToken } from "@/api/gen/model";
import { Details, ErrorText, Field, Icon, Sheet } from "@/components/ui";
import { seen } from "@/lib/format";
import { useAction } from "@/lib/hooks";

const REFRESH = ["/api/devices/"];

/** What a device's token is good for, in the admin's words. Shown wherever a token appears. */
export const TOKEN_HINT = "Copy this onto the device now. We won't show it again — if it goes missing, rotate the token.";

type SheetProps = { open: boolean; device: Device | null; onClose: () => void };

/** The token, once. Copying it is the whole point of the sheet, so the copy button leads. */
export function TokenSheet({ open, name, token, onClose, children }: {
  open: boolean; name: string; token: string; onClose: () => void; children?: React.ReactNode;
}) {
  const [copied, setCopied] = useState(false);
  useEffect(() => { setCopied(false); }, [token]);
  async function copy() {
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
    } catch {
      setCopied(false); // no clipboard (an old browser, or no permission): the token is on screen to read
    }
  }
  return (
    <Sheet open={open} onClose={onClose} title={`${name}'s token`} closable={false}>
      <div className="rl-checkcode">
        <p className="rl-row__title" style={{ wordBreak: "break-all" }}>{token}</p>
        <p className="rl-row__meta">Device token</p>
      </div>
      {/* The one accent action: copying the token is the reason this sheet exists. */}
      <button className="rl-button rl-button--accent rl-button--block" type="button" style={{ marginTop: "var(--space-3)" }} onClick={copy}>
        <Icon as={copied ? Check : Copy} />{copied ? "Copied" : "Copy Token"}
      </button>
      <p className="rl-field__hint">{TOKEN_HINT}</p>
      <div className="rl-sheet__actions">
        {children ?? <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Done</button>}
      </div>
    </Sheet>
  );
}

/** A device's details and the three things you can do to it. */
export function DeviceSheet({ open, device, onClose, onPick }: SheetProps & { onPick: (step: "rename" | "rotate" | "off") => void }) {
  return (
    <Sheet open={open} onClose={onClose} title={device?.name ?? "Device"}>
      <Details rows={[
        { icon: Building2, label: "Branch", value: device?.branch_name },
        { icon: Hash, label: "Serial number", value: device?.serial },
        { icon: Clock, label: "Last punch", value: seen(device?.last_seen) },
        { icon: Power, label: "Status", value: device?.is_active ? "On" : "Switched off" },
      ]} />
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" onClick={() => onPick("rename")}>Rename</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => onPick("rotate")}>Rotate Token</button>
        {device?.is_active && (
          <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" onClick={() => onPick("off")} aria-haspopup="dialog">Deactivate</button>
        )}
      </div>
    </Sheet>
  );
}

export function RenameSheet({ open, device, onClose }: SheetProps) {
  const [name, setName] = useState("");
  const [err, setErr] = useState<string>();
  const a = useAction();
  useEffect(() => { if (open && device) { setName(device.name); setErr(undefined); } }, [open, device]);
  async function save() {
    if (!name.trim()) return setErr("Give the device a name");
    setErr(undefined);
    try {
      await a.run(`/api/devices/${device!.id}/`, { name: name.trim() }, { method: "PATCH", refresh: REFRESH });
      onClose();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Rename device">
      <p className="rl-row__meta">The name is how you tell your devices apart. The serial number stays as it is.</p>
      <Field label="Device name" error={err}>
        {(id) => <input className="rl-field__input" id={id} value={name} placeholder="Front turnstile" enterKeyHint="go" onChange={(e) => setName(e.target.value)} />}
      </Field>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Saving…" : "Save Changes"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Cancel</button>
      </div>
    </Sheet>
  );
}

/** Rotating asks first: the device stops letting people in until the new token is on it. */
export function RotateSheet({ open, device, onClose, onToken }: SheetProps & { onToken: (d: DeviceWithToken) => void }) {
  const a = useAction();
  async function rotate() {
    try {
      const d = await a.run<DeviceWithToken>(`/api/devices/${device!.id}/rotate-token/`, undefined, { refresh: REFRESH });
      onToken(d!);
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title={`Rotate ${device?.name ?? "device"}'s token?`}>
      <p className="rl-row__meta">The token it uses now stops working at once, so nobody gets in on that device until you set the new one on it.</p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={rotate}>{a.busy ? "Rotating…" : "Rotate Token"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Cancel</button>
      </div>
    </Sheet>
  );
}

export function DeactivateSheet({ open, device, onClose }: SheetProps) {
  const a = useAction();
  async function off() {
    try {
      await a.run(`/api/devices/${device!.id}/deactivate/`, undefined, { refresh: REFRESH });
      onClose();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title={`Switch off ${device?.name ?? "this device"}?`}>
      <p className="rl-row__meta">It stops letting people in straight away, and the check-ins it recorded stay. A device is never deleted, so it keeps its place in this list.</p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={off}>{a.busy ? "Switching off…" : "Deactivate"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep It On</button>
      </div>
    </Sheet>
  );
}
