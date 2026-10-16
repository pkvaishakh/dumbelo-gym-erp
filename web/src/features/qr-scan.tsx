"use client";
import { useEffect, useRef, useState } from "react";

/** Camera QR scanner (html5-qrcode). Calls onCode once with the text of the first code it reads. */
export function QrScanner({ onCode }: { onCode: (text: string) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const done = useRef(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let stop: (() => Promise<void>) | null = null;
    let cancelled = false;
    (async () => {
      const { Html5Qrcode } = await import("html5-qrcode");
      if (cancelled || !box.current) return;
      const scanner = new Html5Qrcode(box.current.id, { verbose: false });
      try {
        await scanner.start({ facingMode: "environment" }, { fps: 10, qrbox: { width: 240, height: 240 } }, (text) => {
          if (done.current) return;
          done.current = true;
          onCode(text);
        }, () => {});
        stop = () => scanner.stop().catch(() => {});
      } catch {
        setError("Allow camera access to scan, or ask the front desk to check you in.");
      }
    })();
    return () => { cancelled = true; stop?.(); };
  }, [onCode]);
  return (
    <>
      <div id="rl-qr-reader" ref={box} className="rl-card" style={{ overflow: "hidden", minHeight: 280 }} />
      {error && <p className="rl-field__hint">{error}</p>}
    </>
  );
}

/** The branch code inside a wall QR: https://app/checkin/<code> or just <code>. */
export function codeFrom(text: string) {
  const m = text.match(/checkin\/([A-Za-z0-9_-]+)/);
  return m ? m[1]! : text.trim();
}
