"use client";

import { useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import type { Me, Role } from "@/api/gen/model";
import { api, ApiError, gymSlug, onPaused, onSignedOut, tokens } from "./api";

export type RoleName = "admin" | "receptionist" | "trainer" | "member";

type Session = {
  me: Me;
  role: Role & { role: RoleName };
  gym: string;
  /** Dumbelo has suspended this gym: everyone sees the paused screen, and its admins can still open More. */
  paused: boolean;
  /** Admin's chosen branch (null = all branches). Always null for everyone else: they see all their branches. */
  branch: number | null;
  branchName: string;
  setBranch: (id: number | null) => void;
  switchGym: (slug: string) => void;
  signOut: () => void;
};

/** Who is signed in, for the frame the gym app and the Console share: the avatar and the account sheets. */
type Who = { me: Me; signOut: () => void; moreHref: string };

const Ctx = createContext<Session | null>(null);
const WhoCtx = createContext<Who | null>(null);
const BRANCH = "rl.branch";
const ME = ["/api/me/"];

export function useSession() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useSession outside SessionProvider");
  return s;
}

export function useWho() {
  const w = useContext(WhoCtx);
  if (!w) throw new Error("useWho outside SessionProvider or ConsoleProvider");
  return w;
}

export async function signIn(username: string, password: string) {
  const t = await api<{ access: string; refresh: string }>("/api/auth/login/", { method: "POST", json: { username: username.trim().replace(/^@+/, ""), password } });
  tokens.set(t.access, t.refresh);
}

/** Loads who is signed in, and sends people without a session to sign-in. Both providers start here. */
function useSignedIn() {
  const router = useRouter();
  const qc = useQueryClient();
  const [ready, setReady] = useState(false);

  const signOut = useCallback(() => {
    const refresh = tokens.refresh;
    // Tell the API so this refresh token stops working; leave right away whether or not that call gets through.
    if (refresh) api("/api/auth/logout/", { method: "POST", json: { refresh } }).catch(() => {});
    tokens.clear();
    qc.clear();
    router.replace("/login");
  }, [qc, router]);

  useEffect(() => {
    const toLogin = () => router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`);
    onSignedOut.handler = () => { qc.clear(); toLogin(); };
    // A gym suspended while someone is using it: ask again who they are, and the paused screen takes over.
    onPaused.handler = () => { qc.invalidateQueries({ queryKey: ME }); };
    if (!tokens.access && !tokens.refresh) toLogin();
    else setReady(true);
  }, [qc, router]);

  const meQ = useQuery({ queryKey: ME, queryFn: () => api<Me>("/api/me/"), enabled: ready });
  return { meQ, signOut };
}

/** What to show when /api/me/ can't answer; null while it loads or once it has. */
function trouble(meQ: UseQueryResult<Me>) {
  const signedOut = meQ.error instanceof ApiError && meQ.error.status === 401; // api.ts is already sending them to sign-in
  if (!meQ.isError || meQ.isFetching || signedOut) return null;
  return (
    <div className="rl-root" style={{ padding: 24 }}>
      <h1 className="rl-display">Can&apos;t reach Dumbelo</h1>
      <p className="rl-lede">{meQ.error instanceof ApiError && meQ.error.status ? meQ.error.message : "Check your connection and try again."}</p>
      <button className="rl-button" style={{ marginTop: 24 }} onClick={() => meQ.refetch()}>Try Again</button>
    </div>
  );
}

/** The gym app's session: who, which gym and which branch. Dumbelo admins with no gym of their own go to the Console. */
export function SessionProvider({ children, fallback }: { children: React.ReactNode; fallback: React.ReactNode }) {
  const router = useRouter();
  const qc = useQueryClient();
  const { meQ, signOut } = useSignedIn();
  const [gym, setGym] = useState<string | null>(null);
  const [branch, setBranchState] = useState<number | null>(null);
  const consoleOnly = !!meQ.data?.is_dumbelo_admin && !meQ.data.roles.length;

  useEffect(() => { if (consoleOnly) router.replace("/console"); }, [consoleOnly, router]);

  useEffect(() => {
    const me = meQ.data;
    if (!me) return;
    if (!me.roles.length) return;
    const stored = gymSlug.get();
    const pick = me.roles.find((r) => r.gym === stored) ?? me.roles[0]!;
    if (pick.gym !== stored) gymSlug.set(pick.gym);
    setGym(pick.gym);
    let b: number | null = null;
    try { b = Number(localStorage.getItem(BRANCH)) || null; } catch { /* ignore */ }
    const ids = pick.branches.map((x) => x.id);
    // Only admins pick a branch; everyone else sees all of their own branches (the API keeps them there).
    setBranchState(pick.role === "admin" && b && ids.includes(b) ? b : null);
  }, [meQ.data]);

  const value = useMemo<Session | null>(() => {
    const me = meQ.data;
    if (!me || !gym) return null;
    const role = me.roles.find((r) => r.gym === gym);
    if (!role) return null;
    const admin = role.role === "admin";
    const bName = branch ? role.branches.find((b) => b.id === branch)?.name ?? ""
      : admin ? "All branches" : role.branches.map((b) => b.name).join(", ");
    return {
      me,
      role: role as Session["role"],
      gym,
      paused: role.gym_status === "suspended",
      branch,
      branchName: bName,
      setBranch: (id) => {
        if (!admin) return;
        setBranchState(id);
        try { if (id) localStorage.setItem(BRANCH, String(id)); else localStorage.removeItem(BRANCH); } catch { /* ignore */ }
      },
      switchGym: (slug) => {
        gymSlug.set(slug);
        try { localStorage.removeItem(BRANCH); } catch { /* ignore */ }
        qc.clear();
        window.location.assign("/home");
      },
      signOut,
    };
  }, [meQ.data, gym, branch, qc, signOut]);
  const who = useMemo(() => (value ? { me: value.me, signOut, moreHref: "/more" } : null), [value, signOut]);

  if (consoleOnly) return <>{fallback}</>;
  if (meQ.data && !meQ.data.roles.length) {
    return (
      <div className="rl-root" style={{ padding: 24 }}>
        <h1 className="rl-display">No gym yet</h1>
        <p className="rl-lede">Your account isn&apos;t part of any gym. Ask your gym&apos;s admin to add you.</p>
        <button className="rl-button" style={{ marginTop: 24 }} onClick={signOut}>Sign Out</button>
      </div>
    );
  }
  const problem = trouble(meQ);
  if (problem) return problem;
  if (!value || !who) return <>{fallback}</>;
  return <WhoCtx.Provider value={who}><Ctx.Provider value={value}>{children}</Ctx.Provider></WhoCtx.Provider>;
}

/** The Console's session: Dumbelo admins only. Anyone else is sent to their gym. */
export function ConsoleProvider({ children, fallback }: { children: React.ReactNode; fallback: React.ReactNode }) {
  const router = useRouter();
  const { meQ, signOut } = useSignedIn();
  const me = meQ.data;
  const allowed = !!me?.is_dumbelo_admin;
  useEffect(() => { if (me && !allowed) router.replace("/home"); }, [me, allowed, router]);
  const who = useMemo(() => (me ? { me, signOut, moreHref: "/console/more" } : null), [me, signOut]);
  const problem = trouble(meQ);
  if (problem) return problem;
  if (!who || !allowed) return <>{fallback}</>;
  return <WhoCtx.Provider value={who}>{children}</WhoCtx.Provider>;
}
