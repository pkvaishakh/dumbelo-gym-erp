"use client";
import { Printer } from "lucide-react";
import { useParams } from "next/navigation";
import QRCode from "qrcode";
import { useEffect, useState } from "react";

import { useBranchesRetrieve } from "@/api/gen/branches/branches";
import { DetailBar } from "@/components/shell";
import { Icon, Mark } from "@/components/ui";
import { useSession } from "@/lib/session";

/** The poster for the wall by the entrance. Members and staff scan it to check themselves in. */
export default function BranchQr() {
  const { id } = useParams<{ id: string }>();
  const { role } = useSession();
  const b = useBranchesRetrieve(Number(id)).data?.data;
  const [svg, setSvg] = useState("");
  const url = b ? `${window.location.origin}/checkin/${b.qr_code}` : "";
  useEffect(() => { if (url) QRCode.toString(url, { type: "svg", margin: 1, errorCorrectionLevel: "M", color: { dark: "#1b1e1f", light: "#ffffff" } }).then(setSvg); }, [url]);
  return (
    <div className="rl-app rl-root">
      <div className="rl-noprint"><DetailBar title="Check-in QR" /></div>
      <main className="rl-app__main">
        <div className="rl-card rl-card--pad rl-poster" style={{ textAlign: "center", marginTop: "var(--space-4)" }}>
          <span className="rl-logo" style={{ justifyContent: "center" }}><Mark /><span className="rl-logo__name">{role.gym_name}</span></span>
          <h2 className="rl-display" style={{ marginTop: "var(--space-4)" }}>Scan to check in</h2>
          <p className="rl-lede">{b?.name} branch. Open your phone&apos;s camera and point it here.</p>
          <div style={{ width: "min(320px, 80vw)", margin: "var(--space-6) auto" }} dangerouslySetInnerHTML={{ __html: svg }} />
          <p className="rl-row__meta" style={{ wordBreak: "break-all" }}>{url}</p>
        </div>
        <button className="rl-button rl-button--block rl-noprint" type="button" style={{ marginTop: "var(--space-4)" }} onClick={() => window.print()}><Icon as={Printer} />Print</button>
      </main>
    </div>
  );
}
