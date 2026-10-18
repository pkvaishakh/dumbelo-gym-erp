"use client";
/* Add Account and Edit Account: one task, the edit filled in (the design's Edit… rule). */
import { Banknote, Landmark } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";

import { useAccountsList } from "@/api/gen/accounts/accounts";
import type { Account } from "@/api/gen/model";
import { TaskBar } from "@/components/shell";
import { Choices, Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { day, rupees, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";
import { useSession } from "@/lib/session";

import { MONEY } from "./money";
import { ActionBar } from "./sell";

type Kind = "bank" | "cash";
const KINDS = [
  { value: "bank" as Kind, title: "Bank account", meta: "Where branches' UPI, card and bank money goes", icon: Landmark },
  { value: "cash" as Kind, title: "Cash in hand", meta: "The cash at one branch's desk", icon: Banknote },
];

export function AccountForm({ account, kind: startKind, branch: startBranch }: { account?: Account; kind?: Kind; branch?: number }) {
  const { role } = useSession();
  const editing = !!account;
  const all = useAccountsList().data?.data ?? [];
  const [f, setF] = useState({
    kind: (account?.kind ?? startKind ?? "bank") as Kind, name: account?.name ?? "", bank_name: account?.bank_name ?? "", account_number: account?.account_number ?? "",
    ifsc: account?.ifsc ?? "", opening: account ? String((account.opening_balance_paise ?? 0) / 100) : "",
    branch: account?.branch ?? (startKind === "cash" ? startBranch : undefined) ?? 0,
    branches: account?.branches ?? (startKind !== "cash" && startBranch ? [startBranch] : []),
  });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Account | null>(null);
  const firstRef = useRef<HTMLInputElement>(null);
  const a = useAction();
  const cash = f.kind === "cash";
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => { setF({ ...f, [k]: e.target.value }); setErrs({ ...errs, [k]: "" }); };
  const err = (k: string) => errs[k] || fieldError(a.error, k === "opening" ? "opening_balance_paise" : k);

  // Who uses which bank account now, so the form can say when picking a branch moves it from another one.
  const usedBy = new Map(all.filter((x) => x.kind === "bank" && x.id !== account?.id).flatMap((x) => (x.branches ?? []).map((b) => [b, x.label] as const)));
  const hasCash = new Set(all.filter((x) => x.kind === "cash").map((x) => x.branch));
  const cashBranches = role.branches.filter((b) => !hasCash.has(b.id) || b.id === account?.branch);
  const moving = f.branches.filter((b) => usedBy.has(b)).map((b) => `${role.branches.find((x) => x.id === b)?.name} moves from ${usedBy.get(b)}`);

  async function save() {
    const e: Record<string, string> = {};
    if (cash && !f.branch) e.branch = "Choose the branch whose cash this is";
    if (!cash) {
      if (!f.name.trim()) e.name = "Name it, like HDFC current account";
      if (!f.bank_name.trim()) e.bank_name = "Enter the bank's name";
      if (!/^\d{6,20}$/.test(f.account_number.replace(/\s/g, ""))) e.account_number = "Use the account number's digits, 6 to 20 of them";
      if (f.ifsc.trim() && !/^[A-Za-z]{4}0[A-Za-z0-9]{6}$/.test(f.ifsc.trim())) e.ifsc = "Use the 11-character IFSC from a cheque, like HDFC0001234";
    }
    if (f.opening.trim() && toPaise(f.opening) < 0) e.opening = "Enter 0 or more";
    setErrs(e);
    if (Object.keys(e).length) { if (e.name) firstRef.current?.focus(); return; }
    const body = cash
      ? { kind: f.kind, opening_balance_paise: toPaise(f.opening), ...(editing ? {} : { branch: f.branch }) }
      : { ...(editing ? {} : { kind: f.kind }), name: f.name.trim(), bank_name: f.bank_name.trim(), account_number: f.account_number.replace(/\s/g, ""),
          ifsc: f.ifsc.trim().toUpperCase(), opening_balance_paise: toPaise(f.opening), branches: f.branches };
    try {
      const out = await a.run<Account>(editing ? `/api/accounts/${account!.id}/` : "/api/accounts/", body, { method: editing ? "PATCH" : "POST", refresh: MONEY });
      setSaved(out ?? null);
    } catch { /* shown */ }
  }

  const title = editing ? "Edit Account" : cash ? "Set Up Cash" : "Add Account";
  const openingHint = editing
    ? `What it held on ${day(account!.opened_on)}, when it was added. Changing it moves the balance by the same amount.`
    : cash ? "Count the cash at the desk now. Cash payments and expenses recorded from now on move it." : "What the account holds today. Money recorded from now on moves it.";
  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title={title} />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          {!editing && (
            <fieldset className="rl-fieldset"><legend>What it is</legend>
              <Choices name="acct-kind" two value={f.kind} onChange={(v) => { setF({ ...f, kind: v }); setErrs({}); a.clearError(); }} options={KINDS} />
            </fieldset>
          )}
          {cash ? (
            <fieldset className="rl-fieldset"><legend>Branch</legend>
              {editing ? <p className="rl-row__title">{account!.branch_name}</p> : cashBranches.length ? (
                <div className="rl-chips">{cashBranches.map((b) => (
                  <label className="rl-chipopt" key={b.id}><input type="radio" name="acct-branch" checked={f.branch === b.id} onChange={() => { setF({ ...f, branch: b.id }); setErrs({ ...errs, branch: "" }); }} /><span>{b.name}</span></label>
                ))}</div>
              ) : <p className="rl-row__meta">Every branch&apos;s cash is set up already.</p>}
              <ErrorText>{err("branch")}</ErrorText>
            </fieldset>
          ) : (
            <>
              <Field label="Name" error={err("name")} hint="What you call it, so it's easy to pick.">{(id, desc) => (
                <input ref={firstRef} className="rl-field__input" id={id} aria-describedby={desc} maxLength={80} placeholder="HDFC current account" enterKeyHint="next" value={f.name} onChange={set("name")} />
              )}</Field>
              <Field label="Bank" error={err("bank_name")}>{(id, desc) => (
                <input className="rl-field__input" id={id} aria-describedby={desc} maxLength={80} placeholder="HDFC Bank" autoComplete="off" enterKeyHint="next" value={f.bank_name} onChange={set("bank_name")} />
              )}</Field>
              <Field label="Account number" error={err("account_number")}>{(id, desc) => (
                <input className="rl-field__input" id={id} aria-describedby={desc} inputMode="numeric" autoComplete="off" maxLength={24} placeholder="50200012345678" enterKeyHint="next"
                  value={f.account_number} onChange={set("account_number")} />
              )}</Field>
              <Field label="IFSC" optional error={err("ifsc")}>{(id, desc) => (
                <input className="rl-field__input" id={id} aria-describedby={desc} autoCapitalize="characters" autoCorrect="off" spellCheck={false} autoComplete="off" maxLength={11} placeholder="HDFC0001234"
                  value={f.ifsc} onChange={set("ifsc")} />
              )}</Field>
              <fieldset className="rl-fieldset"><legend>Branches that use it <span className="rl-optional">(optional)</span></legend>
                <div className="rl-chips">{role.branches.map((b) => (
                  <label className="rl-chipopt" key={b.id}><input type="checkbox" checked={f.branches.includes(b.id)}
                    onChange={(e) => setF({ ...f, branches: e.target.checked ? [...f.branches, b.id] : f.branches.filter((x) => x !== b.id) })} /><span>{b.name}</span></label>
                ))}</div>
                <ErrorText>{err("branches")}</ErrorText>
                <p className="rl-field__hint">{moving.length ? `${moving.join(". ")}. A branch uses one bank account; ` : "A branch uses one bank account, and branches can share one. "}
                  Their new UPI, card and bank payments go in, and their bank expenses come out. Pick none for an account no branch uses, like the owner&apos;s reserve.</p>
              </fieldset>
            </>
          )}
          <fieldset className="rl-fieldset"><legend>Opening balance</legend>
            <label className={`rl-amount${err("opening") ? " is-invalid" : ""}`}><span aria-hidden="true">₹</span>
              <input type="number" inputMode="decimal" min={0} aria-label="Opening balance in rupees" placeholder="0" value={f.opening} onChange={set("opening")} />
            </label>
            {err("opening") ? <ErrorText>{err("opening")}</ErrorText> : <p className="rl-field__hint">{openingHint}</p>}
          </fieldset>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label={editing ? "Save Changes" : title} onClick={save} busy={a.busy} />
      <Sheet open={!!saved} onClose={() => {}} closable={false}>
        {saved && (
          <>
            <Confirm title={editing ? "Changes saved" : `${saved.label} added`}
              text={`Balance ${rupees(saved.balance_paise)}. ${saved.kind === "cash" ? `Cash payments and expenses at ${saved.branch_name} move it from now on.`
                : saved.branch_names.length ? `New UPI, card and bank payments at ${saved.branch_names.join(" and ")} go into it.` : "No branch uses it yet: money moves in and out only when you move it."}`} />
            <div className="rl-sheet__actions">
              <Link className="rl-button rl-button--block" href={`/money/accounts/${saved.id}`}>Done</Link>
              {!editing && <Link className="rl-button rl-button--secondary rl-button--block" href="/money">Back to Cash and Bank</Link>}
            </div>
          </>
        )}
      </Sheet>
    </div>
  );
}
