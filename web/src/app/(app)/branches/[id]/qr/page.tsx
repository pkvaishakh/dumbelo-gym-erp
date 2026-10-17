"use client";
import { Download, Printer } from "lucide-react";
import { useParams } from "next/navigation";
import QRCode from "qrcode";
import { useEffect, useState } from "react";

import { useBranchesRetrieve } from "@/api/gen/branches/branches";
import { DetailBar } from "@/components/shell";
import { Icon, Mark } from "@/components/ui";
import { useSession } from "@/lib/session";

const INK = "#1b1e1f";

/** The poster as a PNG (1200 × 1600, sharp enough for A4): gym name, heading, branch, QR and its link. */
async function posterPng(gym: string, branch: string, url: string) {
  await document.fonts.ready;
  const font = getComputedStyle(document.body).fontFamily;
  const W = 1200, H = 1600, c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d")!;
  g.fillStyle = "#ffffff"; g.fillRect(0, 0, W, H);
  g.fillStyle = INK; g.textAlign = "center"; g.textBaseline = "alphabetic";
  g.font = `700 48px ${font}`; g.fillText(gym, W / 2, 150);
  g.font = `800 96px ${font}`; g.fillText("Scan to check in", W / 2, 300);
  g.font = `400 40px ${font}`; g.fillText(`${branch} branch. Open your phone's camera and point it here.`, W / 2, 380, W - 120);
  const qr = new Image();
  qr.src = await QRCode.toDataURL(url, { width: 820, margin: 1, errorCorrectionLevel: "M", color: { dark: INK, light: "#ffffff" } });
  await qr.decode();
  g.drawImage(qr, (W - 820) / 2, 460, 820, 820);
  g.font = `400 32px ${font}`; g.fillText(url, W / 2, 1400, W - 120);
  return new Promise<Blob>((ok) => c.toBlob((b) => ok(b!), "image/png"));
}

/** The poster for the wall by the entrance. Members and staff scan it to check themselves in. */
export default function BranchQr() {
  const { id } = useParams<{ id: string }>();
  const { role } = useSession();
  const b = useBranchesRetrieve(Number(id)).data?.data;
  const [svg, setSvg] = useState("");
  const url = b ? `${window.location.origin}/checkin/${b.qr_code}` : "";
  useEffect(() => { if (url) QRCode.toString(url, { type: "svg", margin: 1, errorCorrectionLevel: "M", color: { dark: INK, light: "#ffffff" } }).then(setSvg); }, [url]);
  async function download() {
    if (!b) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(await posterPng(role.gym_name, b.name, url));
    a.download = `check-in-qr-${b.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}.png`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
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
        <button className="rl-button rl-button--secondary rl-button--block rl-noprint" type="button" style={{ marginTop: "var(--space-3)" }} disabled={!svg} onClick={download}><Icon as={Download} />Download</button>
      </main>
    </div>
  );
}
