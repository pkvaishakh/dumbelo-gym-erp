import type { Metadata } from "next";

import { DESCRIPTION, TITLE } from "@/features/landing/content";
import { Landing } from "@/features/landing/Landing";

/* The public front page, and the one page meant for search. Signed-in people reach the app at /home (where the
 * installed app opens, too). */
export const metadata: Metadata = {
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: "/" },
  robots: { index: true, follow: true, googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 } },
  openGraph: {
    type: "website", url: "/", siteName: "Dumbelo", locale: "en_IN", title: TITLE,
    description: "Members, plans, payments, check-ins, staff and money for every branch, in one app on your phone. Made for gyms in India.",
  },
  twitter: { card: "summary_large_image", title: TITLE, description: "Gym management software made for India: members, payments, check-ins and WhatsApp reminders in one app." },
};

export default function Index() {
  return <Landing />;
}
