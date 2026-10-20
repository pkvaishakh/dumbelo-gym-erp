import { ImageResponse } from "next/og";

/* The picture a link to Dumbelo shows on WhatsApp, LinkedIn and X: the brand line on ink, the logo's plates in volt.
 * Drawn at build time. Colours are the design tokens' values (ink, on-ink, volt): CSS variables don't
 * reach this renderer. */
export const alt = "Dumbelo: gym management software made for India. Open up. Check in. Close out.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = "#1b1e1f";
const ON_INK = "#ffffff";
const VOLT = "#1eb960";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: INK, color: ON_INK }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {/* The mark's on-ink version: a volt tile with ink plates (dumbelo-mark.svg, recoloured as the Logo allows). */}
          <svg width="88" height="88" viewBox="0 0 40 40">
            <rect width="40" height="40" rx="12" fill={VOLT} />
            <rect x="9.5" y="15" width="5" height="10" rx="2.5" fill={INK} />
            <rect x="17.5" y="12" width="5" height="16" rx="2.5" fill={INK} />
            <rect x="25.5" y="9" width="5" height="22" rx="2.5" fill={INK} />
          </svg>
          <div style={{ fontSize: 44, fontWeight: 700 }}>Dumbelo</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", fontSize: 104, fontWeight: 700, lineHeight: 1, letterSpacing: -3 }}>
          <span>Open up.</span><span>Check in.</span><span>Close out.</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 32, color: ON_INK }}>
          <div style={{ width: 40, height: 14, borderRadius: 7, background: VOLT }} />
          <span>Gym management software made for India</span>
        </div>
      </div>
    ),
    size,
  );
}
