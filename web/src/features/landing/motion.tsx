"use client";
/* The landing page's few interactive parts. Everything they wrap is rendered on the server and arrives as
 * children, so only these small pieces run in the browser. */
import { Check, MessageCircle, Minus } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Icon, Mark } from "@/components/brand";
import { tokens } from "@/lib/api";
import { CHAT_TEXT, SALES_WHATSAPP, whatsappLink } from "@/lib/site";

import type { ROLES } from "./content";
import s from "./landing.module.css";
import type { Role } from "./phones";

const calm = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = () => window.matchMedia("(hover: hover) and (pointer: fine)").matches;

/** Turns the element toward the pointer: --rx and --ry (degrees, up to ±max) while the pointer is over it, or over
 *  its closest ancestor matching `within`. */
function useTilt<T extends HTMLElement>(max: number, within?: string) {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    const area = (within ? el?.closest<HTMLElement>(within) : null) ?? el;
    if (!el || !area || calm() || !finePointer()) return;
    let frame = 0;
    const move = (e: PointerEvent) => {
      const r = area.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        el.style.setProperty("--ry", (x * max * 2).toFixed(2));
        el.style.setProperty("--rx", (-y * max * 2).toFixed(2));
      });
    };
    const leave = () => { cancelAnimationFrame(frame); el.style.setProperty("--ry", "0"); el.style.setProperty("--rx", "0"); };
    area.addEventListener("pointermove", move);
    area.addEventListener("pointerleave", leave);
    return () => { cancelAnimationFrame(frame); area.removeEventListener("pointermove", move); area.removeEventListener("pointerleave", leave); };
  }, [max, within]);
  return ref;
}

/** The page. Marks each [data-reveal] block with data-in once it scrolls into view, so it can settle into place. */
export function MotionRoot({ children }: { children: React.ReactNode }) {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const items = el.querySelectorAll<HTMLElement>("[data-reveal]");
    if (calm() || !("IntersectionObserver" in window)) return;
    el.setAttribute("data-motion", "");
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.setAttribute("data-in", ""); io.unobserve(e.target); }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    items.forEach((i) => {
      // Already on screen when the page loads (a link to #demo): show it as it is, without the settle.
      if (i.getBoundingClientRect().top < window.innerHeight) i.setAttribute("data-in", "");
      else io.observe(i);
    });
    return () => io.disconnect();
  }, []);
  return <div ref={root} className={`${s.page} rl-root`}>{children}</div>;
}

export function Header({ children }: { children: React.ReactNode }) {
  const [signedIn, setSignedIn] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    setSignedIn(!!tokens.access);
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header className={s.header} data-scrolled={scrolled || undefined}>
      <div className={`${s.wrap} ${s.headerIn}`}>
        <Link className="rl-logo" href="/" aria-label="Dumbelo home"><Mark /><span className="rl-logo__name">Dumbelo</span></Link>
        {children}
        <div className={s.headerActions}>
          {signedIn
            ? <Link className="rl-button rl-button--secondary rl-button--sm" href="/home">Open App</Link>
            : <Link className="rl-button rl-button--secondary rl-button--sm" href="/login">Sign In</Link>}
          <a className={`rl-button rl-button--sm ${s.headerDemo}`} href="#demo">Book a Free Demo</a>
        </div>
      </div>
    </header>
  );
}

/** The hero's scene: turns with the pointer anywhere over the hero, and leans back as the hero scrolls away. */
export function HeroStage({ children }: { children: React.ReactNode }) {
  const scene = useTilt<HTMLDivElement>(7, "section");
  useEffect(() => {
    const section = scene.current?.closest("section");
    if (!section || calm()) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const r = section.getBoundingClientRect();
      section.style.setProperty("--away", Math.min(1, Math.max(0, -r.top / Math.max(1, r.height))).toFixed(3));
    };
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => { window.removeEventListener("scroll", onScroll); cancelAnimationFrame(frame); };
  }, [scene]);
  return <div className={s.stage} aria-hidden="true"><div ref={scene} className={s.scene}>{children}</div></div>;
}

/** A card that settles in when it scrolls into view (the outer box) and turns toward the pointer (the inner one). */
export function TiltCard({ children, className = "", outer = "", i = 0, max = 6 }: {
  children: React.ReactNode; className?: string; outer?: string; i?: number; max?: number;
}) {
  const ref = useTilt<HTMLDivElement>(max);
  return (
    <div className={outer} data-reveal style={{ "--i": i } as React.CSSProperties}>
      <div ref={ref} className={`${s.tilt} ${className}`}>{children}</div>
    </div>
  );
}

/** Your team: the role chosen turns the phone to that role's home. The phones come rendered from the server. */
export function RoleSwitcher({ roles, phones }: { roles: typeof ROLES; phones: Record<Role, React.ReactNode> }) {
  const [role, setRole] = useState<Role>("desk");
  const r = roles.find((x) => x.id === role)!;
  const turn = useTilt<HTMLDivElement>(8);
  return (
    <div className={s.roles} data-reveal>
      <div className={s.rolesCopy}>
        <div className="rl-seg rl-seg--block rl-seg--onsurface" role="group" aria-label="Show the app for">
          {roles.map((x) => (
            <button key={x.id} className="rl-seg__btn" type="button" aria-pressed={x.id === role} onClick={() => setRole(x.id)}>{x.tab}</button>
          ))}
        </div>
        <div className={s.roleText} key={role} aria-live="polite">
          <h3 className={s.roleTitle}>{r.title}</h3>
          <p className={s.cardText}>{r.line}</p>
          <p className={s.checksHead}>{r.cant.length ? "Can" : "Can do everything, including"}</p>
          <ul className={s.checks}>
            {r.can.map((c) => <li key={c}><span className={s.checkYes}><Icon as={Check} size="xs" /></span>{c}</li>)}
          </ul>
          {r.cant.length > 0 && (
            <>
              <p className={s.checksHead}>Kept from them</p>
              <ul className={s.checks}>
                {r.cant.map((c) => <li key={c} className={s.checkNo}><span className={s.checkNoMark}><Icon as={Minus} size="xs" /></span>{c}</li>)}
              </ul>
            </>
          )}
        </div>
      </div>
      <div className={s.roleStage}>
        <div ref={turn} className={s.roleTurn}>
          <div className={s.roleFlip} key={role}>{phones[role]}</div>
        </div>
      </div>
    </div>
  );
}

/** Two ways to reach Dumbelo that stay in reach as the page scrolls: the chat on WhatsApp button (every size, when
 *  sales has a number), and on a phone the demo bar once the hero has gone. The chat button lifts above the bar
 *  rather than sitting on it. Both step aside while the demo section is on screen, and the chat button while any
 *  other WhatsApp button is: one is enough. */
export function ReachUs() {
  const [seen, setSeen] = useState({ hero: true, form: false, chat: false });
  useEffect(() => {
    const hero = document.getElementById("top");
    const form = document.getElementById("demo");
    if (!hero || !form || !("IntersectionObserver" in window)) return;
    // Other WhatsApp buttons on the page (pricing's) say so with data-chat-here; this one makes way for them.
    const others = [...document.querySelectorAll("[data-chat-here]")];
    const showing = new Set<Element>();
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) showing.add(e.target); else showing.delete(e.target);
      setSeen({ hero: showing.has(hero), form: showing.has(form), chat: others.some((o) => showing.has(o)) });
    });
    showing.add(hero);
    [hero, form, ...others].forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
  const bar = !seen.hero && !seen.form;
  const away = seen.form || seen.chat;
  return (
    <>
      {SALES_WHATSAPP && (
        <a className={s.chat} href={whatsappLink(CHAT_TEXT.general)} target="_blank" rel="noopener noreferrer"
          aria-label="Chat with Dumbelo on WhatsApp" data-lifted={bar || undefined} data-away={away || undefined}
          tabIndex={away ? -1 : undefined}>
          <Icon as={MessageCircle} />
          <span className={s.chatShort} aria-hidden="true">WhatsApp</span>
          <span className={s.chatLong} aria-hidden="true">Chat on WhatsApp</span>
        </a>
      )}
      <div className={s.sticky} data-show={bar || undefined} aria-hidden={!bar} inert={!bar}>
        <a className="rl-button rl-button--block" href="#demo">Book a Free Demo</a>
      </div>
    </>
  );
}
