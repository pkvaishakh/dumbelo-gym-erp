"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { PriceList } from "@/api/gen/model";
import { usePlatformPricesList } from "@/api/gen/platform/platform";
import { TaskBar } from "@/components/shell";
import { Confirm, ErrorText, Field, Sheet } from "@/components/ui";
import { ActionBar } from "@/features/sell";
import { day, gymToday, toPaise } from "@/lib/format";
import { fieldError, useAction } from "@/lib/hooks";

const PRICES = [
  { key: "base_paise", label: "Base fee, a month", hint: "Every gym pays it, whatever its size." },
  { key: "per_branch_paise", label: "Per branch, a month", hint: "For each branch a gym's plan has room for, open or not." },
  { key: "whatsapp_setup_paise", label: "WhatsApp setup", hint: "Once, when a gym's WhatsApp is set up." },
  { key: "machine_setup_paise", label: "Attendance machine setup", hint: "Once, for each machine." },
  { key: "utility_message_paise", label: "Reminder or receipt message", hint: "Each one delivered from Dumbelo's number (Meta's utility category)." },
  { key: "marketing_message_paise", label: "Offer message", hint: "Each one delivered from Dumbelo's number (Meta's marketing category)." },
  { key: "authentication_message_paise", label: "Sign-in code message", hint: "Each one delivered from Dumbelo's number (Meta's authentication category)." },
] as const;
type Key = (typeof PRICES)[number]["key"];

const asRupees = (paise: number) => String(paise / 100);

/** Add Price List: new prices from a day on. Price lists are never edited, and no gym moves to them by itself. */
export default function NewPricesPage() {
  const router = useRouter();
  const today = gymToday("Asia/Kolkata");
  const current = usePlatformPricesList().data?.data.results.find((p) => p.is_current);
  const [f, setF] = useState<Record<Key, string> | null>(null);
  const [from, setFrom] = useState(today);
  const [note, setNote] = useState("");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [made, setMade] = useState<PriceList | null>(null);
  const a = useAction();
  // Start from today's prices, so changing one price is one field.
  const values = f ?? (Object.fromEntries(PRICES.map((p) => [p.key, current ? asRupees(current[p.key]) : ""])) as Record<Key, string>);
  const err = (k: string) => errs[k] ?? fieldError(a.error, k);

  async function save() {
    const e: Record<string, string> = {};
    for (const p of PRICES) if (values[p.key].trim() === "" || Number.isNaN(Number(values[p.key]))) e[p.key] = "Enter the price in rupees, or 0";
    if (!from) e.active_from = "Pick the day these prices start";
    else if (from < today) e.active_from = "Pick today or a later day";
    setErrs(e);
    if (Object.keys(e).length) return;
    const body = { active_from: from, note: note.trim(), ...Object.fromEntries(PRICES.map((p) => [p.key, toPaise(values[p.key])])) };
    try { setMade((await a.run<PriceList>("/api/platform/prices/", body, { refresh: ["/api/platform/"] }))!); } catch { /* shown */ }
  }

  return (
    <div className="rl-app rl-app--task rl-root">
      <TaskBar title="Add Price List" />
      <main className="rl-app__main">
        <form className="rl-form" noValidate onSubmit={(e) => { e.preventDefault(); save(); }}>
          <Field label="Starts on" error={err("active_from")} hint="Gyms keep their prices until you move each one, from its Dumbelo plan.">
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="date" min={today} value={from} onChange={(e) => setFrom(e.target.value)} />}
          </Field>
          {PRICES.map((p) => (
            <Field key={p.key} label={p.label} prefix="₹" error={err(p.key)} hint={p.hint}>
              {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} type="text" inputMode="decimal" autoComplete="off" value={values[p.key]}
                onChange={(e) => setF({ ...values, [p.key]: e.target.value.replace(/[^\d.]/g, "") })} />}
            </Field>
          ))}
          <Field label="Note" optional error={err("note")} hint="For Dumbelo's team: why the prices changed.">
            {(id, d) => <input className="rl-field__input" id={id} aria-describedby={d} value={note} maxLength={200} placeholder="New prices for 2027" onChange={(e) => setNote(e.target.value)} />}
          </Field>
          <ErrorText>{a.error && !a.error.fields ? a.error.message : undefined}</ErrorText>
        </form>
      </main>
      <ActionBar label="Add Price List" busy={a.busy} busyLabel="Adding…" onClick={save} />
      <Sheet open={!!made} onClose={() => router.push("/console/prices")} closable={false}>
        {made && (
          <>
            <Confirm title={`Prices from ${day(made.active_from)} added`}
              text="No gym pays them yet. Open a gym and use Move to Current Prices on its Dumbelo plan once they start." />
            <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" onClick={() => router.push("/console/prices")}>Done</button></div>
          </>
        )}
      </Sheet>
    </div>
  );
}
