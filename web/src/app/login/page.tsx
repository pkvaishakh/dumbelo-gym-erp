"use client";
import { Eye, EyeOff } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Barbell, ErrorText, Icon, Mark } from "@/components/ui";
import type { Me } from "@/api/gen/model";
import { api, ApiError, tokens } from "@/lib/api";
import { signIn } from "@/lib/session";

export default function LoginPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [id, setId] = useState("");
  const [pw, setPw] = useState("");
  const [show, setShow] = useState(false);
  const [errors, setErrors] = useState<{ id?: string; pw?: string; form?: string }>({});
  const [state, setState] = useState<"idle" | "busy" | "done">("idle");
  const idRef = useRef<HTMLInputElement>(null);
  const pwRef = useRef<HTMLInputElement>(null);

  const nextPath = (home = "/home") => {
    const n = new URLSearchParams(window.location.search).get("next");
    return n && n.startsWith("/") && !n.startsWith("//") ? n : home;
  };
  useEffect(() => { if (tokens.access) router.replace(nextPath()); }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const next: typeof errors = {};
    if (!id.trim()) next.id = "Enter your username";
    if (!pw) next.pw = "Enter your password";
    setErrors(next);
    if (next.id) return idRef.current?.focus();
    if (next.pw) return pwRef.current?.focus();
    setState("busy");
    try {
      await signIn(id.trim(), pw);
      const me = await api<Me>("/api/me/");
      qc.setQueryData(["/api/me/"], me); // the app needs it next: no second trip
      setState("done");
      router.replace(nextPath(me.is_dumbelo_admin ? "/console" : "/home")); // Dumbelo admins land on the Console
    } catch (err) {
      setState("idle");
      setErrors({ form: err instanceof ApiError ? err.message : "Can't reach Dumbelo. Check your connection and try again." });
    }
  }

  return (
    <main className="rl-auth rl-root">
      <aside className="rl-auth__brand" aria-hidden="true">
        <div className="rl-auth__brand-art"><div className="rl-barbell rl-barbell--lg rl-barbell--on-ink rl-barbell--bleed rl-barbell--load"><span className="rl-barbell__tip" /><span className="rl-plate rl-plate--sm" /><span className="rl-plate rl-plate--md" /><span className="rl-plate rl-plate--lg" /><span className="rl-plate" /><span className="rl-plate rl-plate--volt" /><span className="rl-barbell__collar" /><span className="rl-barbell__shaft" /></div></div>
        <div>
          <p className="rl-auth__brand-line"><span>Open up.</span> <span>Check in.</span> <span>Close out.</span></p>
          <p className="rl-auth__brand-note">Members, check-ins and payments in one app, for every role in the gym.</p>
        </div>
      </aside>
      <div className="rl-auth__app">
        <header className="rl-auth__top"><span className="rl-logo"><Mark /><span className="rl-logo__name">Dumbelo</span></span></header>
        <div className="rl-auth__art"><Barbell load /></div>
        <section className="rl-auth__body" aria-labelledby="rl-title">
          <h1 className="rl-display" id="rl-title">Let&apos;s get moving</h1>
          <p className="rl-lede">Sign in to manage your gym</p>
          <form className="rl-auth__form" noValidate onSubmit={submit}>
            <div className={`rl-field${errors.id ? " is-invalid" : ""}`}>
              <label className="rl-field__label" htmlFor="rl-id">Username</label>
              <div className="rl-field__control">
                <input ref={idRef} className="rl-field__input" id="rl-id" name="username" type="text" inputMode="email" autoComplete="username" autoCapitalize="none" autoCorrect="off" spellCheck={false} enterKeyHint="next"
                  placeholder="your.username" value={id} aria-invalid={!!errors.id} aria-describedby="rl-id-e"
                  onChange={(e) => { setId(e.target.value); setErrors((x) => ({ ...x, id: undefined, form: undefined })); }}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); pwRef.current?.focus(); } }} />
              </div>
              <ErrorText id="rl-id-e">{errors.id}</ErrorText>
            </div>
            <div className={`rl-field${errors.pw ? " is-invalid" : ""}`}>
              <label className="rl-field__label" htmlFor="rl-pw">Password</label>
              <div className="rl-field__control">
                <input ref={pwRef} className="rl-field__input" id="rl-pw" name="password" type={show ? "text" : "password"} autoComplete="current-password" autoCapitalize="none" autoCorrect="off" spellCheck={false} enterKeyHint="go"
                  placeholder="Enter your password" value={pw} aria-invalid={!!errors.pw} aria-describedby="rl-pw-e"
                  onChange={(e) => { setPw(e.target.value); setErrors((x) => ({ ...x, pw: undefined, form: undefined })); }} />
                <button className="rl-field__toggle" type="button" aria-label={show ? "Hide password" : "Show password"} aria-pressed={show} onClick={() => setShow(!show)}>
                  <Icon as={show ? EyeOff : Eye} />
                </button>
              </div>
              <ErrorText id="rl-pw-e">{errors.pw}</ErrorText>
            </div>
            <ErrorText>{errors.form}</ErrorText>
            <button className="rl-button rl-button--block" type="submit" disabled={state !== "idle"} data-state={state}>
              {state === "busy" ? "Signing in…" : state === "done" ? "Signed in" : "Sign In"}
            </button>
          </form>
        </section>
        <footer className="rl-legal" style={{ textAlign: "center", padding: "var(--space-6)" }}>
          <p className="rl-row__meta" style={{ margin: 0 }}>Forgot your username or password? Ask your gym&apos;s front desk.</p>
        </footer>
      </div>
    </main>
  );
}
