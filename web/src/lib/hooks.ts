"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import { api, ApiError } from "./api";
import { invalidate } from "./query";

/** GET for endpoints the generated client types loosely (reports, collection, notes). Same cache keys as orval's. */
export function useGet<T>(url: string, params?: Record<string, string | number | boolean | null | undefined>, enabled = true) {
  const clean = params ? Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")) : undefined;
  const qs = clean && Object.keys(clean).length ? "?" + new URLSearchParams(clean as Record<string, string>).toString() : "";
  return useQuery({ queryKey: clean && Object.keys(clean).length ? [url, clean] : [url], queryFn: () => api<T>(url + qs), enabled });
}

/** Search text to send: trimmed, 300 ms after the last keystroke, and empty below 2 characters. */
export function useSearch(text: string) {
  const [value, setValue] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setValue(text.trim().length >= 2 ? text.trim() : ""), 300);
    return () => clearTimeout(t);
  }, [text]);
  return value;
}

/** Run a change against the API, keep its error message, and refresh the lists it touches. */
export function useAction() {
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const run = useCallback(
    async <T,>(url: string, json?: unknown, opts: { method?: string; refresh?: string[] } = {}): Promise<T | undefined> => {
      setBusy(true);
      setError(null);
      try {
        const out = await api<T>(url, { method: opts.method ?? "POST", json });
        await invalidate(qc, ...(opts.refresh ?? ["/api/"]));
        return out;
      } catch (e) {
        const err = e instanceof ApiError ? e : new ApiError(0, "network", "Can't reach Dumbelo. Check your connection and try again.");
        setError(err);
        throw err;
      } finally {
        setBusy(false);
      }
    },
    [qc],
  );
  return { run, busy, error, clearError: () => setError(null) };
}

type Page<T> = { data: { count: number; next?: string | null; results: T[] } };

/** Options for a generated useXxxListInfinite hook: start at the first page, ask for the next by its offset. */
export const paged = {
  initialPageParam: 0,
  getNextPageParam: (last: Page<unknown>) => {
    if (!last.data.next) return undefined;
    const offset = new URL(last.data.next, "http://x").searchParams.get("offset");
    return offset === null ? undefined : Number(offset);
  },
};

/** The rows loaded so far across pages, and how many there are in all. */
export function pages<T>(q: { data?: { pages: Page<T>[] } }) {
  const all = q.data?.pages ?? [];
  return { rows: all.flatMap((p) => p.data.results), count: all[0]?.data.count ?? 0 };
}

/** First message for a field from an API validation error. */
export function fieldError(err: ApiError | null, field: string): string | undefined {
  const v = err?.fields?.[field];
  if (!v) return undefined;
  return Array.isArray(v) ? String(v[0]) : typeof v === "string" ? v : undefined;
}
