"use client";
import { Check } from "lucide-react";

import { useUsernamesCheckRetrieve } from "@/api/gen/usernames/usernames";
import { Chips, Field, Icon } from "@/components/ui";
import { useDebounced } from "@/lib/hooks";

/** A username as it's stored: no spaces, no leading @, lowercase. */
export const cleanUsername = (v: string) => v.trim().replace(/^@+/, "").toLowerCase();

/** Ask the API about a username as it's typed (and for suggestions from the email or name while it's empty). */
function useCheck(username: string, email?: string, name?: string, enabled = true) {
  const key = useDebounced(JSON.stringify([cleanUsername(username), email?.trim() || undefined, name?.trim() || undefined]));
  const [u, e, n] = JSON.parse(key) as [string, string | undefined, string | undefined];
  const p = { username: u, email: e ?? undefined, name: n ?? undefined };
  const q = useUsernamesCheckRetrieve(p, { query: { enabled: enabled && !!(p.username || p.email || p.name), staleTime: 30_000 } });
  const settled = p.username === cleanUsername(username);
  return settled ? q.data?.data : undefined;
}

/** A new login's username: checked as they type, with free ones to tap when it's taken. Left empty, the API
 *  makes one from the email or name, and the hint says which. */
export function UsernameField({ value, onChange, email, name, error, current, self, label = "Username", optional = true }: {
  value: string; onChange: (v: string) => void; email?: string; name?: string; error?: string; label?: string; optional?: boolean;
  /** The username they have now, when changing it: not "taken". */
  current?: string;
  /** The signed-in person's own: "you" instead of "they". */
  self?: boolean;
}) {
  const who = self ? "You sign in" : "They sign in";
  const typed = cleanUsername(value);
  const unchanged = !!current && typed === current;
  const check = useCheck(value, email, name, !unchanged);
  const suggestions = (!unchanged && check?.suggestions) || [];
  let hint: React.ReactNode = `Letters, numbers, full stops and underscores. ${who} with it.`;
  let problem: string | undefined;
  if (unchanged) hint = `${who} with this username.`;
  else if (!typed && suggestions[0]) hint = <>Leave it empty and they get <b>@{suggestions[0]}</b>.</>;
  else if (typed && check?.available) hint = <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}><Icon as={Check} size="xs" />@{typed} is free</span>;
  else if (typed && check?.problem) problem = check.problem;
  return (
    <>
      <Field label={label} optional={optional} prefix="@" error={error || problem} hint={hint}>{(id, d) => (
        <input className="rl-field__input" id={id} aria-describedby={d} value={value} autoComplete="off" autoCapitalize="none" autoCorrect="off" spellCheck={false}
          inputMode="email" maxLength={31} placeholder={suggestions[0] ?? "meera.iyer"} onChange={(e) => onChange(e.target.value)} />
      )}</Field>
      {typed && !unchanged && !check?.available && suggestions.length > 0 && (
        <Chips name={`${label}-suggest`} label="Free usernames" value={"" as string} onChange={onChange}
          options={suggestions.map((s) => ({ value: s, label: `@${s}` }))} style={{ marginTop: "calc(var(--space-2) * -1)" }} />
      )}
    </>
  );
}

/** Someone who already signs in to Dumbelo (at another gym): their username, and whose login it is, so the right
 *  person is added. Their password and details stay theirs. */
export function ExistingLoginField({ value, onChange, error }: { value: string; onChange: (v: string) => void; error?: string }) {
  const check = useCheck(value);
  const typed = cleanUsername(value);
  const found = typed && check && check.problem === "That username is taken";
  let hint: React.ReactNode = "Ask them for the username they sign in with. Their password stays theirs.";
  let problem: string | undefined;
  if (found && check?.name) hint = <>@{typed} is <b>{check.name}</b>.</>;
  else if (typed && check && !found) problem = "No one signs in with that username";
  return (
    <Field label="Their username" prefix="@" error={error || problem} hint={hint}>{(id, d) => (
      <input className="rl-field__input" id={id} aria-describedby={d} value={value} autoComplete="off" autoCapitalize="none" autoCorrect="off" spellCheck={false}
        inputMode="email" onChange={(e) => onChange(e.target.value)} />
    )}</Field>
  );
}

export type LoginKind = "new" | "existing";

/** New login, or the one they already have at another gym. */
export function LoginKindChips({ value, onChange }: { value: LoginKind; onChange: (v: LoginKind) => void }) {
  return (
    <Chips name="login-kind" label="Their login" scroll={false} value={value} onChange={onChange}
      options={[{ value: "new", label: "New login" }, { value: "existing", label: "Already on Dumbelo" }]} />
  );
}
