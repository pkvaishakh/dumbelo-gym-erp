/* The landing page's words: one place to change them, shared by the page and its structured data for search. */
import {
  BarChart3, ClipboardList, DatabaseBackup, History, IndianRupee, LockKeyhole, MessageCircle, Receipt, Repeat, ShieldCheck,
  Snowflake, Tags, Users, Wallet, type LucideIcon,
} from "lucide-react";

import type { Role } from "./phones";

export const TITLE = "Gym management software for Indian gyms | Dumbelo";
export const DESCRIPTION =
  "Dumbelo is gym management software made for India: members, plans, part payments, UPI, check-ins by QR or turnstile, " +
  "WhatsApp renewal reminders, staff, payroll and every branch in one app on your phone.";

export const ROLES: { id: Role; tab: string; title: string; line: string; can: string[]; cant: string[] }[] = [
  {
    id: "admin", tab: "Owner", title: "Owners and managers",
    line: "Everything in every branch, and the reports to run it.",
    can: ["Plans, offers, staff and payroll", "Reports, expenses, recurring bills, cash and bank", "Correct or void a payment, with the reason kept", "Give tasks to staff and follow them"],
    cant: [],
  },
  {
    id: "desk", tab: "Front desk", title: "Your front desk",
    line: "A busy shift on one screen: find, check in, collect.",
    can: ["Add members, sell plans and record payments", "Check people in by search or scan", "Apply the offers you set", "Count the cash drawer at close"],
    cant: ["Revenue totals, reports or staff pay", "Changing or voiding a payment"],
  },
  {
    id: "trainer", tab: "Trainer", title: "Your trainers",
    line: "Their own members, and who needs a word today.",
    can: ["Their members’ status and phone", "Who has a payment due", "Their tasks, and their own check-in"],
    cant: ["Any amount of money, anywhere"],
  },
  {
    id: "member", tab: "Member", title: "Your members",
    line: "Their own plan, their visits, and the door.",
    can: ["Days left on their plan", "Check in with the wall QR", "Their visits and their streak"],
    cant: ["Anyone else’s details"],
  },
];

/** Ten cards; the two wide ones fill three-across rows exactly. */
export const FEATURES: { icon: LucideIcon; title: string; text: string; wide?: boolean }[] = [
  { icon: Tags, title: "Plans and offers", text: "Monthly, quarterly, personal training add-ons. Take a plan off sale and the members on it keep it until it ends.", wide: true },
  { icon: Receipt, title: "Payments, part by part", text: "UPI, cash, card or bank transfer. Part payments keep the rest as due, never more than owed." },
  { icon: Repeat, title: "Renewals that start on time", text: "A renewal starts the day after the current plan ends, so no one loses a day." },
  { icon: Snowflake, title: "Freeze for travel or exams", text: "Check-in pauses, and the unused days go on the end of the plan." },
  { icon: ClipboardList, title: "Tasks for staff", text: "Give a task with a due date. They start it, post updates and mark it done." },
  { icon: Wallet, title: "Payroll from check-ins", text: "Fixed, by attendance, hourly or daily. Payslips worked out from the days they came." },
  { icon: MessageCircle, title: "WhatsApp, on its own", text: "Renewal and dues reminders, receipts and tasks go out on WhatsApp. Pause them whenever you like.", wide: true },
  { icon: IndianRupee, title: "Cash, bank and expenses", text: "Each drawer’s cash in hand, counted at close. Recurring bills remind you before they’re due." },
  { icon: BarChart3, title: "Reports you can act on", text: "Collection, members, attendance and dues by branch and period. Print or download any of them." },
  { icon: Users, title: "Every branch, one view", text: "Switch branch or see them all. Staff only see the branches they work at." },
];

export const TRUST: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: History, title: "Nothing important is deleted", text: "Payments are voided, members archived, staff deactivated. Every correction is in the audit log with who and why." },
  { icon: ShieldCheck, title: "Each role sees its own part", text: "The server decides what each person may see. A trainer’s phone never receives an amount." },
  { icon: LockKeyhole, title: "Our support waits for you", text: "We see your gym only when you open a support window, read-only, and every look is logged." },
  { icon: DatabaseBackup, title: "Backed up every night", text: "With a restore drill every month, so a backup is known to work before it’s needed." },
];

export const FAQ: [string, string][] = [
  ["Do my members need to install an app?", "No. Dumbelo opens in the phone’s browser, and anyone can add it to their home screen like an app. That goes for your staff too."],
  ["Can members pay online in the app?", "Not yet. Your desk records each payment as it happens, by UPI, cash, card or bank transfer, and the member gets a receipt on WhatsApp."],
  ["I run more than one branch. Does that work?", "Yes. Each branch has its own staff, opening sessions, cash drawer and wall QR, and you see them one at a time or all together."],
  ["Can trainers see what members pay?", "No. A trainer sees their own members, their status and phone, and whether a payment is due, but never an amount."],
  ["What if the desk enters a payment wrong?", "You correct or void it with a reason. The original stays on record in the audit log, so the history always adds up."],
  ["Can someone from Dumbelo see my members?", "Only if you open a support window for them. It is read-only, it ends when you say, and every look is logged."],
  ["What does the demo involve?", "A call at a time that suits you. We show Dumbelo with plans and branches like yours, answer your questions, and if it fits, set up your gym with you."],
];
