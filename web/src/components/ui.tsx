"use client";
/* Small building blocks that render the Rackline design system's markup (src/styles/rackline.css). */
import { AlertCircle, Check, ChevronRight, Plus, Search, SlidersHorizontal, X, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useId, useRef } from "react";

import { initials, STATUS_LABEL } from "@/lib/format";

export function Icon({ as: C, size }: { as: LucideIcon; size?: "sm" | "xs" }) {
  return <C className={`rl-icon${size ? ` rl-icon--${size}` : ""}`} strokeWidth={1.75} aria-hidden="true" />;
}

/** The round ink "+" at the end of an app bar that opens a create screen: `href` for a page, `onClick` for a sheet.
 * `label` is what a screen reader hears ("Add Member"). */
export function AddButton({ label, ...to }: { label: string } & ({ href: string } | { onClick: () => void })) {
  const icon = <Icon as={Plus} size="sm" />;
  return "href" in to
    ? <Link className="rl-iconbtn rl-iconbtn--primary" href={to.href} aria-label={label}>{icon}</Link>
    : <button className="rl-iconbtn rl-iconbtn--primary" type="button" aria-label={label} aria-haspopup="dialog" onClick={to.onClick}>{icon}</button>;
}

export function Mark({ className = "rl-logo__mark" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" aria-hidden="true">
      <rect className="rl-logo__tile" width="40" height="40" rx="12" />
      <rect className="rl-logo__plate" x="9.5" y="15" width="5" height="10" rx="2.5" />
      <rect className="rl-logo__plate" x="17.5" y="12" width="5" height="16" rx="2.5" />
      <rect className="rl-logo__plate" x="25.5" y="9" width="5" height="22" rx="2.5" />
    </svg>
  );
}

export function Barbell({ onInk, load }: { onInk?: boolean; load?: boolean }) {
  return (
    <div className={`rl-barbell rl-barbell--bleed${onInk ? " rl-barbell--on-ink" : ""}${load ? " rl-barbell--load" : ""}`} aria-hidden="true">
      <span className="rl-barbell__tip" /><span className="rl-plate rl-plate--sm" /><span className="rl-plate rl-plate--md" />
      <span className="rl-plate rl-plate--lg" /><span className="rl-plate" /><span className="rl-plate rl-plate--volt" />
      <span className="rl-barbell__collar" /><span className="rl-barbell__shaft" />
    </div>
  );
}

export function Photo({ name, size }: { name: string; size?: "lg" | "xl" }) {
  return <span className={`rl-photo${size ? ` rl-photo--${size}` : ""}`} aria-hidden="true">{initials(name)}</span>;
}

export function Status({ status }: { status: string }) {
  const cls = status === "none" ? "off" : status;
  return <span className={`rl-status rl-status--${cls}`}>{STATUS_LABEL[status] ?? status}</span>;
}

export function TaskStatus({ status, overdue }: { status: string; overdue?: boolean }) {
  if (overdue) return <span className="rl-status rl-status--tk-overdue">Overdue</span>;
  const label = status === "doing" ? "In progress" : status === "done" ? "Done" : "To do";
  return <span className={`rl-status rl-status--tk-${status}`}>{label}</span>;
}

export function Section({ title, aside, children, label }: { title?: string; aside?: React.ReactNode; children: React.ReactNode; label?: string }) {
  return (
    <section className="rl-section" aria-label={title ? undefined : label}>
      {title && (
        <div className="rl-section__head">
          <h2 className="rl-section__title">{title}</h2>
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}

/** A figure card. `accent` puts the icon on an ink plate (volt icon) for the lead figure; `share` (0–1) adds a volt
 *  bar under the label, which the `note` must say in words. */
export function Stat({ icon, value, label, note, href, accent, share }: {
  icon: LucideIcon; value: React.ReactNode; label: string; note?: React.ReactNode; href?: string; accent?: boolean; share?: number;
}) {
  const body = (
    <>
      <span className="rl-stat__icon" style={accent ? { background: "var(--ink)", color: "var(--volt)" } : undefined}><Icon as={icon} size="sm" /></span>
      <p className="rl-stat__value">{value}</p>
      <p className="rl-stat__label">{label}</p>
      {share !== undefined && (
        <span className="rl-bar" aria-hidden="true" style={{ marginTop: "var(--space-2)", background: "var(--surface)" }}>
          <span className="rl-bar__fill" style={{ ["--v" as string]: share }} />
        </span>
      )}
      {note && <p className="rl-stat__note">{note}</p>}
    </>
  );
  return href ? <Link className="rl-stat rl-pressable" href={href}>{body}</Link> : <div className="rl-stat">{body}</div>;
}

export function ErrorText({ children, id }: { children?: React.ReactNode; id?: string }) {
  if (!children) return null;
  return (
    <p className="rl-field__error" id={id} role="alert">
      <Icon as={AlertCircle} size="xs" />
      <span>{children}</span>
    </p>
  );
}

type FieldProps = {
  label: string;
  error?: string;
  optional?: boolean;
  hint?: React.ReactNode;
  prefix?: string;
  /** The control is a textarea: the box grows with it instead of one line high. */
  area?: boolean;
  children: (id: string, describedBy?: string) => React.ReactNode;
};
export function Field({ label, error, optional, hint, prefix, area, children }: FieldProps) {
  const id = useId();
  return (
    <div className={`rl-field${error ? " is-invalid" : ""}`}>
      <label className="rl-field__label" htmlFor={id}>
        {label} {optional && <span className="rl-optional">(optional)</span>}
      </label>
      <div className={`rl-field__control${area ? " rl-field__control--area" : ""}`}>
        {prefix && <span className="rl-field__prefix">{prefix}</span>}
        {children(id, error ? `${id}-e` : undefined)}
      </div>
      <ErrorText id={`${id}-e`}>{error}</ErrorText>
      {hint && !error && <p className="rl-field__hint">{hint}</p>}
    </div>
  );
}

export function Chips<T extends string>({ name, value, onChange, options, label, scroll = true, style }: {
  name: string; value: T; onChange: (v: T) => void; label: string; scroll?: boolean; style?: React.CSSProperties;
  options: { value: T; label: string; count?: number }[];
}) {
  return (
    <div className={`rl-chips${scroll ? " rl-chips--scroll" : ""}`} role="radiogroup" aria-label={label} style={style}>
      {options.map((o) => (
        <label className="rl-chipopt" key={o.value}>
          <input type="radio" name={name} value={o.value} checked={value === o.value} onChange={() => onChange(o.value)} />
          <span>{o.label}{o.count !== undefined && <small>{o.count}</small>}</span>
        </label>
      ))}
    </div>
  );
}

export function Seg<T extends string>({ value, onChange, options, label, block = true, onSurface }: {
  value: T; onChange: (v: T) => void; label: string; block?: boolean; onSurface?: boolean;
  options: { value: T; label: string }[];
}) {
  return (
    <div className={`rl-seg${block ? " rl-seg--block" : ""}${onSurface ? " rl-seg--onsurface" : ""}`} role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} className="rl-seg__btn" type="button" aria-pressed={value === o.value} onClick={() => onChange(o.value)}>{o.label}</button>
      ))}
    </div>
  );
}

export function Choices<T extends string | number>({ name, value, onChange, options, two }: {
  name: string; value: T | null; onChange: (v: T) => void; two?: boolean;
  options: { value: T; title: string; meta?: string; price?: string; icon?: LucideIcon }[];
}) {
  return (
    <div className={`rl-choices${two ? " rl-choices--2" : ""}`}>
      {options.map((o) => (
        <label className="rl-choice" key={String(o.value)}>
          <input type="radio" name={name} checked={value === o.value} onChange={() => onChange(o.value)} />
          <span className="rl-choice__box">
            {o.icon && <Icon as={o.icon} />}
            <span className="rl-choice__mark"><Icon as={Check} size="xs" /></span>
            <span className="rl-choice__text">
              <span className="rl-row__title">{o.title}</span>
              {o.meta && <span className="rl-row__meta">{o.meta}</span>}
            </span>
            {o.price && <span className="rl-choice__price">{o.price}</span>}
          </span>
        </label>
      ))}
    </div>
  );
}

export function Sheet({ open, onClose, title, children, closable = true }: {
  open: boolean; onClose: () => void; title?: string; children: React.ReactNode; closable?: boolean;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  // Callers often pass a fresh onClose each render; keeping it in a ref stops the effect below from re-running
  // on every keystroke, which would pull focus out of the field being typed in.
  const closeRef = useRef(onClose);
  useEffect(() => { closeRef.current = onClose; }, [onClose]);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && closable) closeRef.current(); };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); prev?.focus?.(); };
  }, [open, closable]);
  return (
    <>
      <div className={`rl-scrim${open ? " is-open" : ""}`} onClick={closable ? onClose : undefined} />
      <div ref={ref} tabIndex={-1} className={`rl-sheet${open ? " is-open" : ""}`} role="dialog" aria-modal="true" aria-labelledby={title ? id : undefined} aria-hidden={!open}>
        <span className="rl-sheet__grab" aria-hidden="true" />
        {title ? (
          <div className="rl-sheet__head">
            <h2 className="rl-section__title" id={id}>{title}</h2>
            {closable && <button className="rl-iconbtn rl-iconbtn--plain" type="button" onClick={onClose} aria-label="Close"><Icon as={X} /></button>}
          </div>
        ) : closable ? (
          <div className="rl-sheet__head" style={{ justifyContent: "flex-end", marginBottom: "calc(var(--space-8) * -1)" }}>
            <button className="rl-iconbtn rl-iconbtn--plain" type="button" onClick={onClose} aria-label="Close"><Icon as={X} /></button>
          </div>
        ) : null}
        {open && children}
      </div>
    </>
  );
}

export function Confirm({ title, text, blocked }: { title: React.ReactNode; text?: React.ReactNode; blocked?: boolean }) {
  return (
    <div className="rl-confirm">
      <span className={`rl-confirm__mark${blocked ? " rl-confirm__mark--blocked" : ""}`} aria-hidden="true"><Icon as={blocked ? X : Check} /></span>
      <h2 className="rl-confirm__title">{title}</h2>
      {text && <p className="rl-confirm__text">{text}</p>}
    </div>
  );
}

export function Empty({ icon, title, text, children }: { icon: LucideIcon; title: string; text?: string; children?: React.ReactNode }) {
  return (
    <div className="rl-empty">
      <span className="rl-empty__icon" aria-hidden="true"><Icon as={icon} /></span>
      <h2 className="rl-empty__title">{title}</h2>
      {text && <p className="rl-empty__text">{text}</p>}
      {children && <div className="rl-empty__actions">{children}</div>}
    </div>
  );
}

/** The design's "Load More" under a paged list. Hidden once every row is loaded. */
export function LoadMore({ q }: { q: { hasNextPage: boolean; isFetchingNextPage: boolean; fetchNextPage: () => unknown } }) {
  if (!q.hasNextPage) return null;
  return (
    <button className="rl-button rl-button--secondary rl-button--block rl-listmore" type="button" disabled={q.isFetchingNextPage} onClick={() => q.fetchNextPage()}>
      {q.isFetchingNextPage ? "Loading…" : "Load More"}
    </button>
  );
}

export function SkeletonRows({ n = 5 }: { n?: number }) {
  return (
    <ul className="rl-card rl-mlist rl-mlist--compact" aria-busy="true" aria-label="Loading">
      {Array.from({ length: n }, (_, i) => (
        <li key={i}><div className="rl-mrow"><span className="rl-photo rl-skel" /><span className="rl-skel" style={{ height: 14, width: "60%" }} /><span className="rl-skel" style={{ height: 12, width: "40%" }} /></div></li>
      ))}
    </ul>
  );
}

/** `filter` adds the design's sliders button at the end; `on` shows its volt dot while a filter differs from the default. */
export function SearchField({ value, onChange, placeholder, label, autoFocus, filter }: {
  value: string; onChange: (v: string) => void; placeholder: string; label: string; autoFocus?: boolean;
  filter?: { on: boolean; onClick: () => void };
}) {
  return (
    <div className="rl-searchfield">
      <Search className="rl-icon rl-icon--sm rl-searchfield__lead" strokeWidth={1.75} aria-hidden="true" />
      <input className="rl-searchfield__input" type="search" inputMode="search" enterKeyHint="search" autoComplete="off" autoCapitalize="none" autoCorrect="off" spellCheck={false}
        placeholder={placeholder} aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} autoFocus={autoFocus} />
      {value && <button className="rl-searchfield__btn" type="button" aria-label="Clear search" onClick={() => onChange("")}><Icon as={X} size="sm" /></button>}
      {filter && (
        <button className={`rl-searchfield__btn${filter.on ? " is-on" : ""}`} type="button" aria-haspopup="dialog" aria-label={filter.on ? "Filters, some on" : "Filters"} onClick={filter.onClick}>
          <Icon as={SlidersHorizontal} />
        </button>
      )}
    </div>
  );
}

export function MenuRow({ icon, title, value, href, onClick }: { icon: LucideIcon; title: string; value?: React.ReactNode; href?: string; onClick?: () => void }) {
  const inner = (
    <>
      <span className="rl-chipicon" aria-hidden="true"><Icon as={icon} size="sm" /></span>
      <span className="rl-remind__text"><span className="rl-row__title">{title}</span></span>
      {value !== undefined && <span className="rl-menu__value">{value}</span>}
      <Icon as={ChevronRight} size="sm" />
    </>
  );
  return <li>{href ? <Link className="rl-remind__row" href={href}>{inner}</Link> : <button className="rl-remind__row" type="button" onClick={onClick}>{inner}</button>}</li>;
}

/** A setting that takes effect the moment it is flipped, so it never has a Save button (the design's Switch). */
export function Setting({ title, note, name, checked, onChange, disabled }: {
  title: string; note?: React.ReactNode; name: string; checked: boolean; onChange: (on: boolean) => void; disabled?: boolean;
}) {
  return (
    <label className="rl-setting">
      <span className="rl-setting__text">
        <span className="rl-row__title">{title}</span>
        {note && <span className="rl-row__meta">{note}</span>}
      </span>
      <span className="rl-switch">
        <input type="checkbox" role="switch" name={name} checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
        <span />
      </span>
    </label>
  );
}

export function Details({ rows }: { rows: { icon: LucideIcon; label: string; value: React.ReactNode }[] }) {
  return (
    <dl className="rl-card rl-details">
      {rows.map((r) => (
        <div className="rl-detail" key={r.label}>
          <span className="rl-chipicon" aria-hidden="true"><Icon as={r.icon} size="sm" /></span>
          <dt>{r.label}</dt>
          <dd>{r.value || "Not added"}</dd>
        </div>
      ))}
    </dl>
  );
}
