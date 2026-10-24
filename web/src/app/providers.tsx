"use client";
import { QueryClientProvider } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

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

/** A new release reaches phones that keep the app open for days. Look for one when the app comes back to the screen
 * and every 30 minutes; once its service worker takes over (sw.ts: skipWaiting, clientsClaim), the next screen opened
 * loads afresh with the new CSS and JS. Never mid-screen, so a half-filled form isn't lost. */
function useAppUpdates() {
  const path = usePathname();
  const stale = useRef(false);
  useEffect(() => {
    const sw = navigator.serviceWorker;
    if (!sw) return;
    let controlled = !!sw.controller;  // the first install takes over too: that isn't a new release
    const taken = () => { if (controlled) stale.current = true; controlled = true; };
    const check = () => {
      if (document.visibilityState === "visible") sw.getRegistration().then((r) => r?.update()).catch(() => {});  // offline: next time
    };
    sw.addEventListener("controllerchange", taken);
    document.addEventListener("visibilitychange", check);
    const timer = window.setInterval(check, 30 * 60 * 1000);
    return () => {
      sw.removeEventListener("controllerchange", taken);
      document.removeEventListener("visibilitychange", check);
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => { if (stale.current) window.location.reload(); }, [path]);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(makeQueryClient);
  useNoPinchZoom();
  useAppUpdates();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
