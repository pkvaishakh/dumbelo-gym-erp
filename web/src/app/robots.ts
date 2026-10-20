import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";

/* Crawlers may fetch everything, scripts and styles included, so they can render the landing page. The app's own
 * screens say noindex in their metadata, which keeps them out of search better than a Disallow would. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/"] },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
