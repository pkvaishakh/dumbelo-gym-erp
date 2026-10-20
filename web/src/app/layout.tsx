import type { Metadata, Viewport } from "next";

import "./globals.css";
import { SITE_URL } from "@/lib/site";

import { Providers } from "./providers";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Dumbelo",
  description: "Members, check-ins and payments for your gym.",
  applicationName: "Dumbelo",
  appleWebApp: { capable: true, title: "Dumbelo", statusBarStyle: "default" },
  icons: { icon: "/icons/dumbelo-mark.svg", apple: "/icons/icon-192.png" },
  // The app's screens are private and behind sign-in: kept out of search. The landing page asks to be indexed.
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  interactiveWidget: "resizes-content",
  themeColor: "#f3f5ef",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-IN">
      <head>
        <link rel="preload" href="/fonts/Archivo-Variable.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
