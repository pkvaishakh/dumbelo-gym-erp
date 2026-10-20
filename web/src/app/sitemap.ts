import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";

/* The pages meant for search: for now, the landing page. */
export default function sitemap(): MetadataRoute.Sitemap {
  return [{ url: `${SITE_URL}/`, changeFrequency: "monthly", priority: 1 }];
}
