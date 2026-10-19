# Decisions

What was decided, so code and screens stay consistent. Change this file when a decision changes.

## Product
- SaaS for many gyms in India. Billed monthly: a base fee plus a fee per branch (see Rackline billing). Web app /
  PWA only (no native apps yet).
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
  They see their branches' cash in hand, read-only: what each drawer should hold now and today's cash in and out
  (`GET /api/cash/`, on Home and in More), and count it at close. Never the bank: a bank account several branches
  share would show other branches' takings. No revenue totals, reports or staff data, no money moves, refunds or
  settling a count.
- Trainer: their own members' status and phone, and "payment due" without amounts. Their tasks.
- Member: their own membership, visits, and self check-in.
- Rackline support sees a gym only with the gym's time-limited permission (read-only, logged).
- Rackline admins (`User.is_superuser`) run the business side: gyms, their admin accounts, prices, Rackline
  invoices and payments, WhatsApp accounts and templates, when automation runs, and the server's status (health,
  background jobs, messages and webhook, Run Now for the safe-to-repeat jobs). Only they see the server's status:
  not gym admins, and not Rackline support. They use the same sign-in and the same app, landing on
  the Console (`/console`, mobile first, the design system's screens). They never see inside a gym (members,
  payments, check-ins) except through a support window like anyone else on Rackline's team. Their changes are
  audited.
- The Console opens on Home: gyms by status and new this month, what gyms owe Rackline and how much of it is
  overdue, the shared number's messages and amount this month, branch requests waiting, WhatsApp messages delivered,
  failed and waiting today, and whatever on the server is down or whose job's last run failed, with a Needs attention
  card built from these. One summary (`/api/platform/summary/`) in a fixed number of queries; days and months are
  Rackline's (India). It shows counts and Rackline's own money only. Its tabs are Home, Gyms, Server and More; Prices,
  Branch requests, WhatsApp, WhatsApp log and Automation are in More.
- Staff change their own name, email, mobile number and password (More). A member's details are changed by
  the desk. An admin can reset a receptionist's or trainer's password, but not another admin's, and not for
  someone who also signs in to another gym (one login covers every gym); for them, this gym can't change their
  name, email or mobile number either. Any password change signs that person
  out on every other device. Resets are audited; the password never is.

## Money
- Record payments only (no payment gateway in the MVP). Part payments allowed; never more than what's owed.
- Discounts only through offers (percent or amount off, date range, optional plans). Admins correct or void
  payments, with a reason, audited. Nothing is deleted.
- Refunds are money given back to a member for a plan, unlike a void ("the payment never happened"). Admins only,
  audited. A refund names the plan, the amount (never more than was paid for that plan and not refunded yet), how
  it's given back and why; it comes out of the account its branch and method choose, like an expense, and is never
  refused for a low balance. The admin chooses each time: keep the plan (a goodwill refund) or end it today (a plan
  that hasn't started is cancelled, and then all of it must be refunded). Either way the refund lowers what the plan
  costs as much as what was paid, so a refund never makes anyone "payment due". Reports count it as negative
  revenue on the day it's given. A wrong refund is voided with a reason: the money counts as paid again and the plan
  gets its dates back. A plan can be cancelled once what was paid for it is refunded or voided.
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

## Cash and bank (admins; the desk sees and counts its own branches' cash)
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
- An opening balance can be corrected later (audited), but lowering it can't leave the account below zero: the
  money already spent or moved out of it was really there. Raising it is always allowed.
- Accounts are never deleted. One is deactivated only when it holds nothing; its branches are left with no bank
  account until given another. Deactivated accounts stay in the totals: a payment voided later still moves them.
  A payment or expense recorded at the moment an admin deactivates its account is never refused: either it lands
  first and the account isn't empty, or the deactivation goes first and the money is in no balance (checked under
  a lock that the desk's own payments don't wait on).
- Closing the drawer: at the end of the day the desk counts each of its branches' cash (Count Cash) and the app
  shows what it should hold (its balance at that moment) and the difference. One count per branch per day: counting
  again the same day replaces it (audited) until an admin settles it. The desk only counts; an admin settles a
  difference as a deposit (extra cash) or a withdrawal (cash short) with a reason, dated the day counted, so the
  balance stays the sum of what was recorded and is what was counted. Voiding that move opens the difference again.
  A branch's cash must be set up before it can be counted.
- Bank reconciliation: on a bank account's statement an admin ticks each entry that is on the bank's statement too
  (a transfer between two bank accounts is ticked on each side apart), then marks it reconciled up to the last day
  shown at the bank's balance. That balance must equal the balance the account was added with plus every ticked
  entry up to that day; unticked entries are still on their way to the bank. Reconciling locks the ticked entries:
  a reconciled payment, expense or money move can't be corrected (amount, method, branch, date), voided or removed
  until an admin un-reconciles it with a reason (audited). Notes and names can still change. Changing an entry that
  is ticked but not reconciled drops its tick. Each reconciliation is kept (up to, bank balance, who, when).
- Each account has a monthly statement (payments, expenses, refunds and moves, oldest first, with the balance after
  each) to check against the bank's statement or the counted drawer. It downloads as a CSV for the accountant's
  sheet (plain rupees with two decimals, no ₹ or grouping, out as negative, opening and closing balance rows), made
  in the browser from the statement shown, and prints (or saves as a PDF) from a print page like the salary slip.

## Reports (admins; Rackline support may read and download inside its window)
- Reports is a list of categories, each its own screen fetching only its own figures: Revenue, Expenses (salaries
  and bills paid are expenses, so payroll lives here, with what is still owed), Cash and bank, Members, Attendance and
  Tasks. The list shows each category's lead figure and its trend (`GET /api/reports/overview/`).
- One period and one branch for every screen, kept in the URL: 7 days, 30 days, this month, 3 months or custom days.
  A range is at most 3 calendar months (19 Jul to 18 Oct, never 18 Jul; `MAX_MONTHS`) and ends on the gym's today
  or earlier. Default: the last 7 days.
- Trends compare the same number of days just before. Refunds always reduce revenue, on the day they are given.
  Cash and bank compares balances with what they held before the first day; a shared bank account counts once and,
  for one branch, shows whole with the branches it is shared with.
- Statuses on a report's last day follow plan dates and freezes then, but what is owed is as of now. Dues (members'
  and the gym's) are always as of now. Reports only read: they never write expense due dates.
- Each category downloads as a CSV made in the browser from the figures on screen (what it is in the first lines, one
  header row, plain rupees with two decimals; named `<Category> <from> to <to>.csv`) and prints or saves as a PDF from
  a print page, like the statement.

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

## Rackline billing (Rackline admins set it; a gym's admins see it)
- One price list, kept by Rackline admins: a monthly base fee, a monthly fee per branch, a one-time WhatsApp setup
  fee, a one-time attendance machine setup fee (per device), and the rate per delivered message on Rackline's
  shared WhatsApp number (by Meta's message category: utility for reminders and receipts, marketing, authentication).
  All in paise. A price list starts on a day (today or later, one list per day) and is never edited or deleted:
  new prices are a new list. The current list is the latest one that has started, on Rackline's own day (India).
  No gym opens until Rackline has a price list. Gyms that were on Rackline before price lists got a starting list at
  ₹0, with room for the branches they had open, until a Rackline admin moves them to real prices.
- Each gym has its Rackline plan (`GymBilling`): the prices copied from the price list when it was set (a new
  price list never reprices a gym until a Rackline admin moves it), a branch quota, a billing day and its WhatsApp
  mode. The monthly charge is the base fee plus the per-branch fee times the **quota**, not the branches in use,
  so the bill is predictable. It is charged in advance for the month ahead. A new gym starts with room for 1
  branch, on that day's prices, and its billing day is the day it joined (the 28th at most, so every month has
  one). Rackline admins set the quota, billing day and WhatsApp mode from the gym's Rackline plan in the Console.
- A gym opens branches up to its quota. Opening or reactivating one past it is refused ("Your plan has room for 2
  branches. Ask for another one to open this branch."). An admin asks for more from the app (Add Branch to My
  Plan); a Rackline admin approves it, the quota goes up at once, and the rest of the current month is charged
  **pro rata from the day it is approved** (per-branch fee × days left ÷ days in the billing month, rounded to
  the rupee) on the next invoice. A quota is never lowered below the branches in use.
- The billing month runs from the billing day to the day before the next one (billing day 15: 15 Mar to 14 Apr).
  Days left count the approval day itself, in the gym's time zone; half a rupee rounds up. The request keeps the
  days, the rate and the amount, so the invoice shows how it was worked out. A gym has one open request at a time
  (1 to 5 branches, with a note for Rackline); a declined one says why, and the admin can ask again. A Rackline admin
  who is also an admin of the gym can't decide its requests. A closed branch takes no place in the plan, so adding
  one closed is allowed; reopening it needs room.
- Invoices are written monthly on the billing day: the plan for the month ahead, pro-rata branches, one-time setup
  fees, and the previous month's shared WhatsApp usage (delivered billable messages × the rate kept on each
  message). Numbers run in one series per financial year (`RL/2026-27/0001`). No GST yet: every line carries tax
  fields set to zero, so turning GST on later changes no old invoice.
- An invoice is due 7 days after it's written; an open one past that is overdue. Only active gyms are invoiced:
  a gym on trial or suspended on its billing day gets none for that month. A billing month has one invoice, ever:
  running the job again writes nothing, and a voided month isn't written again. An invoice that comes to ₹0 (a
  plan at the starting prices) is paid as it's written. A new billing day takes effect from the next invoice.
- What waits for the next invoice: setup fees and other charges a Rackline admin adds (Add Charge, at the gym's
  own prices unless one is typed; taken back until billed) and the pro-rata cost of each approved request. A
  request approved on or after the billing day of the month being invoiced is already in its quota, so that
  month's branch line counts it once, on its own pro-rata line.
- Voiding an invoice keeps its number and lines and bills nothing again by itself (Add Charge bills what should
  be); an invoice with payments is voided once its payments are. `paid_until` is the last day the gym's paid
  invoices cover, and follows every payment and void. Receipts number like invoices (`RLR/2026-27/0001`).
- Payments to Rackline are recorded by Rackline admins (no payment gateway): part payments allowed, never more than
  the invoice owes, voided with a reason, never deleted. Each payment has a receipt that prints like the salary
  slip. Invoices are voided with a reason, never deleted. Everything here is audited.
- No automatic suspension during the pilot. The owner is reminded before an invoice is due and after it is late;
  a Rackline admin suspends a gym by hand (with a reason) and reactivates it. While a gym is suspended its staff
  and members can't use the app, but its admins can still sign in and see their Rackline plan, invoices and
  receipts. Suspending stops every message the gym would send.

## Messages
- Every WhatsApp message is an approved Meta template, filled with the message's details in order; the words as
  the person read them are kept on the `Message` row so the desk can see them.
- A gym sends from Rackline's shared number (usage billed monthly), from its own Meta WhatsApp Business account
  (it pays Meta itself; Rackline charges the setup only), or not at all. Rackline admins set up accounts, phone
  numbers, credentials and templates; a gym's admins see the number and whether it works, never the credentials.
  Credentials are encrypted in the database (`FIELD_ENCRYPTION_KEY`), write-only, and never in a response, a log
  or the audit log (it says only that they changed).
- A WhatsApp account is a number Rackline sends from: Rackline's shared number (one, belonging to no gym) or a
  gym's own (at most one per gym). It is never deleted. Its status is "not checked yet" until Test Connection,
  which only asks Meta for the number's details (it sends nothing), then "working" or "not working" with Meta's
  reason; new ids or new credentials put it back to "not checked yet". The webhook's verify token is Rackline's
  own, not Meta's, so the Console shows it to type into Meta; a gym's admins never see it.
- Each account has its templates: one per message kind and language may be approved at a time (the sender never
  has to choose), each listing which of the message's details fills `{{1}}`, `{{2}}`… of its approved text. The
  details each message can use are fixed in code (`WhatsAppTemplate.PARAMETERS`). Rackline admins copy a
  template's status from Meta's dashboard by hand; templates are never deleted, only disabled.
- Messages: plan ending in 7 and 3 days, plan ends today, payment due (to members); payment received, the member's
  receipt (**off by default** for each gym); task assigned (to the trainer or receptionist, when an admin assigns
  it); Rackline invoice due and Rackline payment received (to the gym's owner, controlled by Rackline admins).
- Each gym's admins switch each of its messages on or off (pause and resume), in More → Settings → Messages, at
  every branch at once. Pausing stops the messages, not the list, so the desk still sees who to chase. Pausing one
  reminder never stops another: a member whose plan ends today and who owes money hears about the money when "plan
  ends today" is paused. Rackline's two messages to the owner are switched by Rackline admins, per gym, in the
  Console. Every switch is audited. `reminders_on` was replaced by these switches (a gym that had it off got its
  three reminders paused).
- The member's receipt goes after a payment is recorded (once the payment is saved; never for one that didn't save
  or was voided), the task message to the trainer or receptionist when an admin gives them a task, and again to
  whoever it is handed to; an edit sends nothing. A staff member with no mobile number, or who has left, gets none.
- Rackline's messages to a gym's owner (the account owner) go from Rackline's shared number whatever the gym's
  WhatsApp mode, are never billed to the gym, and still go while the gym is suspended (paying is how it opens again).
  An open invoice is chased 3 days before its due day, then 1 and 7 days after it, while anything is still owed, at
  the gym's reminder hour; Rackline payment received goes once a payment is recorded, with the receipt's number.
- When automation runs is Rackline's to set, not the gym's: Rackline admins set one schedule for every gym (the
  reminders' hour, default 6 AM in each gym's own time zone; how many days ahead, default 7 and 3; the hour the
  invoice job runs on a billing day, default just after midnight) and can change the reminders' hour and days
  ahead for one gym (each reminder, and the owner's invoice reminder, can have its own hour for that gym; Use
  Rackline's Times goes back). Whole hours only. A gym's admins see when their messages go out but can't change it.
  A member's one reminder for the day is chosen first, then goes at that reminder's hour. Invoices are written from
  the invoice hour on (a tick missed that hour still writes it later the same day). Retry
  waits (1, 5 and 15 minutes) are fixed in code: they follow Meta's limits, not a business choice. Changes take
  effect on the next run, with no restart, and are audited.
- The daily job writes who needs a nudge (`ReminderDue`) and then sends it. A member gets **one reminder a day** at
  most: a plan ending today comes before money owed, which comes before the 3- and 7-day warnings.
- Nothing is sent twice: every message has a key unique in its gym (a member's reminder for a day, a task's
  assignment, a payment's receipt), and its row is written before it is sent. Nothing goes to someone with no
  number or who asked us to stop (the opt-out on their profile; replying STOP sets it too). A STOP to a gym's own
  number opts out that gym's member; a STOP to Rackline's shared number opts them out at every gym that has messaged
  them from it, and not at gyms that never have. "Stop", "STOP ALL" and "Unsubscribe" count, in any case and with
  any punctuation, as does a Stop button; a longer sentence doesn't. Every reply is kept; the opt-out is audited.
- Delivery follows Meta's webhook: sent, delivered, read or failed, never going back. A failure keeps Meta's code
  and reason. Temporary failures (rate limits, Meta busy) are retried up to 3 times with growing waits; others are
  not. One failure never stops the rest. A message Meta may already have taken (it didn't answer, or our worker
  stopped mid-send) is never retried on its own: sending nothing beats sending twice. Shared-number usage is counted from delivered billable messages, so a
  repeated webhook can't count one twice. A message counts in the billing month Meta says it was delivered (in the
  gym's time zone), at the rate kept on it when it was sent; "read" without a "delivered" before it counts as
  delivered at that time. Meta's word on a message is only taken from the account that sent it. Meta's own
  "billable" flag isn't used: every message delivered from the shared number is billed at the gym's rate, including
  ones Meta doesn't charge Rackline for (such as a utility message inside the member's 24-hour chat window).
  Every signed webhook call is kept, and `manage.py replay_webhook_events` runs kept calls again (a status that came
  before the send saved Meta's id, or a call that broke).
- A gym's admins read every message the gym sent in More → Messages (the desk only its branches' members'), with
  filters and search, and can Retry one that failed. Retry sends the same message again on the same row and key, with
  the same words, to the person's number as it is now, so it still goes once at most: two taps or two admins send it
  once. It is offered only for the gym's own messages that were written out in full and certainly never reached the
  phone, never for one Meta may already have taken (it didn't answer, its answer made no sense, or the send was cut
  off), and is refused while the gym is paused or off, the message is paused, they opted out, have no number, the gym
  now sends from another number, or the template isn't approved. Every Retry is audited.
- Shared-number usage is shown to a gym's admins for its billing month so far (what goes on the invoice written on its
  next billing day), and to Rackline admins per gym per calendar month, each gym's days in its own time zone.
- SMS and email are not in the MVP.

## Stack and hosting
- Backend: Django 5 + DRF + Postgres, JWT (simplejwt), drf-spectacular for OpenAPI. Redis/Celery for jobs (later).
- Frontend: Next.js 15 App Router, TypeScript, Serwist PWA, the design system's CSS, TanStack Query with an
  orval-generated client, date-fns, lucide icons, html5-qrcode, Vitest/Playwright.
- Hosting: AWS Mumbai (ap-south-1) for the API and database — App Runner for the API, RDS Postgres,
  ElastiCache Redis, and the Celery worker and beat on ECS Fargate (App Runner runs HTTP services only).
  The web app on Vercel. Every step, and every setting a server needs, is in `docs/deploy.md`.
- A server runs with `PRODUCTION=true`, which refuses to start without `SECRET_KEY`, `ALLOWED_HOSTS`,
  `DATABASE_URL` and `CACHE_URL`. `/api/health/` is the load balancer's question: no sign-in, no gym.
- The server's status is for Rackline admins only (Console → Server): the version and when it was deployed, the
  database, Redis, the worker (a 2-second ping) and beat (its last tick), each job's last run, messages waiting for a
  retry or failed today, and Meta's webhook calls. Something down shows as down, never as an error. Every scheduled
  job keeps a record of each run (what it did, or why it broke): a run that found nothing to do is kept only as its
  job's latest, the rest for 30 days. Run Now starts reminders, invoices or the webhook replay (the last 7 days'
  calls that couldn't be handled) on the worker: they are safe to repeat, it is refused while that job is waiting
  or running, and it is audited. The retries aren't offered: they run every minute anyway. The webhook replay runs
  only when asked (Run Now, or `manage.py replay_webhook_events`): a call that broke on a bug would only break
  again until the bug is fixed.
- Backups: RDS keeps 14 days, restorable to any second in them, encrypted. Once a month a copy is restored and
  checked against the live database with `manage.py verify_counts` (rows written by the restore time must match:
  nothing is ever deleted, so they can't change after it), then deleted. Steps and the drill log:
  `docs/operations.md`. The old encryption key is kept 14 days after a rotation, so older backups stay readable.
- Open: more languages than English.
