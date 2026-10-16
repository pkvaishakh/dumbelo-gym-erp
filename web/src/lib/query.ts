import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./api";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 2,
        refetchOnWindowFocus: true,
      },
    },
  });
}

/** The URL a cached query is for. Orval keys are [url, params], or ["infinite", url, params] for paged lists. */
export function keyUrl(key: readonly unknown[]): string | undefined {
  const url = key[0] === "infinite" ? key[1] : key[0];
  return typeof url === "string" ? url : undefined;
}

/** Refresh every cached list or record whose URL starts with one of these, after a change. */
export function invalidate(qc: QueryClient, ...prefixes: string[]) {
  return qc.invalidateQueries({
    predicate: (q) => { const url = keyUrl(q.queryKey); return !!url && prefixes.some((p) => url.startsWith(p)); },
  });
}
