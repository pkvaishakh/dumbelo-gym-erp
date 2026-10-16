import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Rackline",
    short_name: "Rackline",
    description: "Members, check-ins and payments for your gym.",
    start_url: "/home",
    display: "standalone",
    background_color: "#f3f5ef",
    theme_color: "#f3f5ef",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
