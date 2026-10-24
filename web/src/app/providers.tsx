"use client";
import { QueryClientProvider } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { makeQueryClient } from "@/lib/query";

/** iOS Safari zooms on a pinch even when the viewport says not to; its gesture events let the app stop it.
 * The landing page (/) stays zoomable. */
function useNoPinchZoom() {
  const path = usePathname();
  useEffect(() => {
    if (path === "/") return;
    const stop = (e: Event) => e.preventDefault();
    document.addEventListener("gesturestart", stop);
    document.addEventListener("gesturechange", stop);
    return () => {
      document.removeEventListener("gesturestart", stop);
      document.removeEventListener("gesturechange", stop);
    };
  }, [path]);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(makeQueryClient);
  useNoPinchZoom();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
