import type { AccountStatement } from "@/api/gen/model";

/** One CSV field: quoted when it holds a comma, a quote or a line break, with quotes doubled. */
function field(v: string | number) {
  const s = String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCsv(rows: (string | number)[][]) {
  return rows.map((r) => r.map(field).join(",")).join("\r\n") + "\r\n";
}

/** Paise as plain rupees for a spreadsheet: "1500.00", "-85000.00". No ₹ and no grouping, so the sheet can add them up. */
export function plainRupees(paise: number) {
  const sign = paise < 0 ? "-" : "";
  const p = Math.abs(paise);
  return `${sign}${Math.floor(p / 100)}.${String(p % 100).padStart(2, "0")}`;
}

const KIND: Record<string, string> = { payment: "Payment", expense: "Expense", refund: "Refund", move: "Money move" };

/** An account's statement for the accountant's sheet: opening balance, each entry with the balance after it, closing balance. */
export function statementCsv(account: string, s: AccountStatement) {
  return toCsv([
    ["Account", "Date", "Type", "Entry", "Details", "Amount (Rs)", "Balance (Rs)", "Reconciled"],
    [account, s.from, "", "Opening balance", "", "", plainRupees(s.opening_paise), ""],
    ...s.entries.map((e) => [account, e.on, KIND[e.kind] ?? e.kind, e.title, e.meta, plainRupees(e.amount_paise), plainRupees(e.balance_paise), e.reconciled ? "Yes" : ""]),
    [account, s.to, "", "Closing balance", "", "", plainRupees(s.closing_paise), ""],
  ]);
}

/** Hand the browser a file to save: Excel opens UTF-8 CSV correctly only with the byte-order mark in front. */
export function download(name: string, csv: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["﻿", csv], { type: "text/csv;charset=utf-8" }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 0);
}
