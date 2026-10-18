/**
 * The one way the app talks to the API. Adds the sign-in token and the gym (X-Gym), refreshes an expired
 * token once, and turns error bodies into ApiError with the API's own message.
 */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const ACCESS = "rl.access";
const REFRESH = "rl.refresh";
const GYM = "rl.gym";

function read(key: string) {
  try {
    return typeof window === "undefined" ? null : window.localStorage.getItem(key);
  } catch {
    return null;
  }
}
function write(key: string, value: string | null) {
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    /* private mode: the session lasts until the tab closes */
  }
}

export const tokens = {
  get access() { return read(ACCESS); },
  get refresh() { return read(REFRESH); },
  set(access: string, refresh?: string) { write(ACCESS, access); if (refresh) write(REFRESH, refresh); },
  clear() { write(ACCESS, null); write(REFRESH, null); write(GYM, null); },
};

export const gymSlug = {
  get: () => read(GYM),
  set: (slug: string) => write(GYM, slug),
};

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public fields?: Record<string, unknown>) {
    super(message);
  }
}

let refreshing: Promise<boolean> | null = null;
async function refreshAccess(): Promise<boolean> {
  const refresh = tokens.refresh;
  if (!refresh) return false;
  refreshing ??= fetch(`${API_URL}/api/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  })
    .then(async (r) => {
      if (!r.ok) return false;
      const body = await r.json();
      tokens.set(body.access, body.refresh);
      return true;
    })
    .catch(() => false)
    .finally(() => { refreshing = null; });
  return refreshing;
}

export const onSignedOut = { handler: () => {} };
/** Called when the API says the gym is suspended, so the app can show its paused screen (session.tsx). */
export const onPaused = { handler: () => {} };

async function send(url: string, init: RequestInit, retry = true): Promise<Response> {
  const headers = new Headers(init.headers);
  const access = tokens.access;
  if (access) headers.set("Authorization", `Bearer ${access}`);
  const gym = gymSlug.get();
  if (gym && !headers.has("X-Gym")) headers.set("X-Gym", gym);
  if (init.body && typeof init.body === "string" && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res = await fetch(url.startsWith("http") ? url : `${API_URL}${url}`, { ...init, headers });
  if (res.status === 401 && !url.includes("/auth/")) {
    if (retry && tokens.refresh && await refreshAccess()) return send(url, init, false);
    // No way to refresh, or still refused with a fresh token (the account is gone): sign in again, never sit on 401s.
    if (tokens.access || tokens.refresh) {
      tokens.clear();
      onSignedOut.handler();
    }
  }
  return res;
}

async function parse(res: Response) {
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

type ErrorBody = { error?: { code: string; message: string; fields?: Record<string, unknown> } };

function failure(res: Response, body: unknown) {
  const err = body && typeof body === "object" ? (body as ErrorBody).error ?? null : null;
  if (res.status === 403 && err?.code === "gym_suspended") onPaused.handler();
  return new ApiError(res.status, err?.code ?? "error", err?.message ?? "Something went wrong. Try again.", err?.fields);
}

/** Plain JSON call: returns the body or throws ApiError. */
export async function api<T = unknown>(url: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, ...rest } = init;
  const res = await send(url, json === undefined ? rest : { ...rest, body: JSON.stringify(json) });
  const body = await parse(res);
  if (!res.ok) throw failure(res, body);
  return body as T;
}

/** Mutator used by the orval-generated client (src/api/gen). Returns { data, status, headers } like orval's fetch client. */
export async function apiFetch<T>(url: string, options: RequestInit): Promise<T> {
  const res = await send(url, options);
  const data = await parse(res);
  if (!res.ok) throw failure(res, data);
  return { data, status: res.status, headers: res.headers } as T;
}
