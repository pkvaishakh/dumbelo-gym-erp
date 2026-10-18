# Decisions

What was decided, so code and screens stay consistent. Change this file when a decision changes.

## Product
- SaaS for many gyms in India. Billing per branch per month. Web app / PWA only (no native apps yet).
- MVP in about 3 months with 2–3 developers; pilot at the current client from week 9.
- One sign-in for every role; the account decides where you land. Staff sign in with email + password;
  members with their phone number + a password the front desk sets.

## Roles
- Admin, Receptionist, Trainer, Member. No branch manager role. Several admins per gym; one is the account owner
  (handles billing, can't be removed). A person can work at several branches, with one role per gym.
- Receptionist: records payments, applies fixed offers only (admins create offers), sees today's collection,
  checks people in, adds members and sells plans. Expenses work like the day's payments: they see and add their
  branches' expenses one day at a time (today's total is on Home, `GET /api/expenses/today/`), so the desk can
  record cash paid out and square it at close. Only admins see longer spans or edit and remove expenses.
  No revenue totals, reports or staff data.
- Trainer: their own members' status and phone, and "payment due" without amounts. Their tasks.
- Member: their own membership, visits, and self check-in.
- Rackline support sees a gym only with the gym's time-limited permission (read-only, logged).
- Staff change their own name, email, mobile number and password (More). A member's details are changed by
  the desk. An admin can reset a receptionist's or trainer's password, but not another admin's, and not for
  someone who also signs in to another gym (one login covers every gym); for them, this gym can't change their
  name, email or mobile number either. Any password change signs that person
  out on every other device. Resets are audited; the password never is.

## Money
- Record payments only (no payment gateway in the MVP). Part payments allowed; never more than what's owed.
- Discounts only through offers (percent or amount off, date range, optional plans). Admins correct or void
  payments, with a reason, audited. Nothing is deleted.
- Plans and offers are one list for the gym, made by admins. Each is given to some branches, or to none, which
  means every branch (including ones opened later). The desk sees and sells only what its branches have; a sale
  checks the plan and the offer against the member's home branch.

## Expenses and payroll (admins only)
- Recurring expenses (rent, utilities, subscriptions) repeat weekly, monthly, every 3 months or yearly from their
  first due date, keeping its day of the month (31st stays the 31st, or the month's last day). Each date is an
  `ExpenseDue`: paid (it becomes an ordinary expense, at whatever the bill came to), skipped, or still due. A due
  shows in Dues and on Home from its reminder day (0 to 30 days before). Dates are fixed once written: to change
  when one is due, stop it and add a new one. Stopping skips the dates still to come; late ones stay.
- Each staff member can have one salary: fixed monthly, monthly by days present (salary × days present ÷ working
  days, never more than the salary; working days are the month less their weekly day off), by the day, or by the
  hour. Hours are never measured (check-in time only), so hourly pay is the rate × their shift's hours × days they
  checked in. A salary can carry fixed monthly allowances and deductions.
- Payroll is worked out per month, never ahead. A draft payslip follows the salary and check-ins until an admin
  approves it; the admin can set days present by hand (a day worked without a check-in, paid leave) and add
  incentives, referral bonuses, allowances or deductions for that month. Approved payslips don't change until
  reopened. Pay is rounded to the rupee, and the take-home pay never drops below zero or below what's already paid.
- Salaries are paid in full or in parts, after approval; daily wages can be paid as the days go. Each payment, like
  each paid bill, is also an expense (Salaries, or the bill's category), so expense totals and reports include them.
  An expense that paid a bill or a salary is changed from Dues or Payroll, never from Expenses.
- Home's "Expense dues" counts bills inside their reminder days and approved salaries not paid in full.
- Referral bonuses are entered on the payslip by hand: members don't record who referred them yet.

## Cash and bank (admins only)
- The gym's money sits in accounts: each branch's cash in hand (one per branch, set up by counting the drawer) and
  bank accounts. A branch uses one bank account; several branches can share one, and an account no branch uses (the
  owner's reserve) is still the gym's money. Admins change which account a branch uses from the account or the branch.
- Every payment and expense keeps the account it hit, chosen when it is recorded from its branch and method: cash
  goes to the branch's cash, UPI, card and bank transfer to the branch's bank account. Moving a branch to another
  account changes where new money goes, never where old money went. Money at a branch whose cash or bank account
  isn't set up is in no balance, and so is money dated before the account was added (its opening balance already
  counts it). Correcting a payment's or an expense's method, branch or date moves it to that account.
- A balance is the opening balance (what it held the day it was added) plus payments in, less expenses out, plus
  money moved in, less money moved out. Voided payments and moves don't count.
- Money moves are deposits (from outside, like the owner adding funds), withdrawals (the owner's drawings, bank
  charges) and transfers between two of the gym's accounts (cash banked, cash drawn, one branch's cash to another).
  They are never income or spending, so reports and expense totals leave them out. Money leaving an account can't
  be more than it holds (checked under a lock), and a move can't be dated before an account was added; a wrong move
  is voided with a reason, and voiding can't leave the account it filled below zero or touch a deactivated one. Payments and expenses are never refused for a low balance: the desk's work goes on.
- Totals count each account once, however many branches share it. A branch shows its bank account's whole balance,
  with the branches it shares it with; a shared balance isn't split between branches.
- Accounts are never deleted. One is deactivated only when it holds nothing; its branches are left with no bank
  account until given another. Deactivated accounts stay in the totals: a payment voided later still moves them.
- Each account has a monthly statement (payments, expenses and moves, oldest first, with the balance after each)
  to check against the bank's statement or the counted drawer.

## Attendance
- Check-in sources: front desk, a fixed wall QR per branch (members/staff scan it), and turnstile/biometric
  (ZKTeco/eSSL pushing punches to `/api/devices/punch/`).
- Only the check-in time is recorded. No check-out, no time inside, no "still in the gym".
- One check-in per person per day. Expired or frozen plans are turned away.
- Branch opening hours are named sessions (add, rename, remove). Attendance and counts are grouped by session;
  members, trainers and receptionists are counted separately.

## Tasks
- Admins assign tasks to trainers and receptionists with a due date (and optional time); staff start them,
  post updates and mark them done; admins see each step and can reopen or delete.

## Messages
- WhatsApp renewal and dues reminders, from Rackline's number first, the gym's own number later. The keys belong
  to the server (`WHATSAPP_PROVIDER` and its two keys), not to a gym.
- The daily 6 AM job writes who needs a nudge (`ReminderDue`) and then sends it. A member gets **one message a
  day** at most: a plan ending today comes before money owed, which comes before the 3- and 7-day warnings.
- Nobody is messaged twice for the same day, with no number, after asking us to stop (the opt-out on their
  profile), or while the gym has reminders off (More → Settings). Turning the gym's switch off stops the
  messages, not the list, so the desk still sees who to chase.
- Every send is kept as a `Message` row with the exact words, so the desk can see what a member read, and a send
  that failed is kept the same way with the provider's reason. One member's failure never stops the morning.
- SMS and email are not in the MVP, and nothing is sent when a payment is recorded (no automatic receipts yet).

## Stack and hosting
- Backend: Django 5 + DRF + Postgres, JWT (simplejwt), drf-spectacular for OpenAPI. Redis/Celery for jobs (later).
- Frontend: Next.js 15 App Router, TypeScript, Serwist PWA, the design system's CSS, TanStack Query with an
  orval-generated client, date-fns, lucide icons, html5-qrcode, Vitest/Playwright.
- Hosting: AWS Mumbai (ap-south-1) for the API and database — App Runner for the API, RDS Postgres,
  ElastiCache Redis, and the Celery worker and beat on ECS Fargate (App Runner runs HTTP services only).
  The web app on Vercel. Every step, and every setting a server needs, is in `docs/deploy.md`.
- A server runs with `PRODUCTION=true`, which refuses to start without `SECRET_KEY`, `ALLOWED_HOSTS`,
  `DATABASE_URL` and `CACHE_URL`. `/api/health/` is the load balancer's question: no sign-in, no gym.
- Open: more languages than English.
