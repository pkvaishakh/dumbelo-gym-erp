"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import type { CheckIn } from "@/api/gen/model";
import { Confirm } from "@/components/ui";
import { ApiError } from "@/lib/api";
import { useAction } from "@/lib/hooks";

import { codeFrom, QrScanner } from "./qr-scan";

/** A member or staff member checking themselves in with the branch's wall QR. */
export function SelfCheckIn({ code }: { code?: string }) {
  const a = useAction();
  const [result, setResult] = useState<CheckIn | null>(null);
  const sent = useRef(false);
  const send = useCallback(async (raw: string) => {
    if (sent.current) return;
    sent.current = true;
    try { setResult((await a.run<CheckIn>("/api/checkins/qr/", { code: codeFrom(raw) }, { refresh: ["/api/checkins/"] }))!); } catch { /* shown */ }
  }, [a]);
  useEffect(() => { if (code) send(code); }, [code, send]);
  const err = a.error as ApiError | null;
  if (result) return (
    <>
      <Confirm title="You’re checked in" text={`${result.time} at ${result.branch_name}. Have a good session.`} />
      <Link className="rl-button rl-button--block" href="/home" style={{ marginTop: "var(--space-6)" }}>Done</Link>
    </>
  );
  if (err) return (
    <>
      <Confirm blocked={err.code !== "already_checked_in"} title={err.code === "already_checked_in" ? "Already checked in" : "Couldn’t check you in"} text={err.message} />
      <div className="rl-sheet__actions" style={{ marginTop: "var(--space-6)" }}>
        {err.code !== "already_checked_in" && !code && <button className="rl-button rl-button--block" type="button" onClick={() => { sent.current = false; a.clearError(); }}>Scan Again</button>}
        <Link className="rl-button rl-button--secondary rl-button--block" href="/home">Back to Home</Link>
      </div>
    </>
  );
  if (code || a.busy) return <p className="rl-row__meta">Checking you in…</p>;
  return (
    <>
      <p className="rl-lede" style={{ marginTop: 0 }}>Point your camera at the Rackline QR code by the entrance.</p>
      <div style={{ marginTop: "var(--space-4)" }}><QrScanner onCode={send} /></div>
    </>
  );
}
