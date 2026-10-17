"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import type { Me, Role } from "@/api/gen/model";
import { api, gymSlug, onSignedOut, tokens } from "./api";

export type RoleName = "admin" | "receptionist" | "trainer" | "member";

type Session = {
  me: Me;
  role: Role & { role: RoleName };
  gym: string;
  /** Admin's chosen branch (null = all branches). Always null for everyone else: they see all their branches. */
  branch: number | null;
  branchName: string;
  setBranch: (id: number | null) => void;
  switchGym: (slug: string) => void;
  signOut: () => void;
};

const Ctx = createContext<Session | null>(null);
const BRANCH = "rl.branch";

export function useSession() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useSession outside SessionProvider");
  return s;
}

export async function signIn(identifier: string, password: string) {
  const t = await api<{ access: string; refresh: string }>("/api/auth/login/", { method: "POST", json: { identifier, password } });
  tokens.set(t.access, t.refresh);
}

/** Loads who is signed in and which gym and branch they're working in. Sends people without a session to sign-in. */
export function SessionProvider({ children, fallback }: { children: React.ReactNode; fallback: React.ReactNode }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [ready, setReady] = useState(false);
  const [gym, setGym] = useState<string | null>(null);
  const [branch, setBranchState] = useState<number | null>(null);

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
    if (!tokens.access && !tokens.refresh) toLogin();
    else setReady(true);
  }, [qc, router]);

  const meQ = useQuery({ queryKey: ["/api/me/"], queryFn: () => api<Me>("/api/me/"), enabled: ready });

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

  if (meQ.data && !meQ.data.roles.length) {
    return (
      <div className="rl-root" style={{ padding: 24 }}>
        <h1 className="rl-display">No gym yet</h1>
        <p className="rl-lede">Your account isn&apos;t part of any gym. Ask your gym&apos;s admin to add you.</p>
        <button className="rl-button" style={{ marginTop: 24 }} onClick={signOut}>Sign Out</button>
      </div>
    );
  }
  if (!value) return <>{fallback}</>;
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
