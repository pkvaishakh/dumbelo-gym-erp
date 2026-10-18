# Roadmap (MVP)

Tick a box when the API, the screen and a test are all in. Decisions behind each item: `docs/decisions.md`.

## Accounts and gyms
- [x] Sign in by email (staff) or phone (member), JWT with refresh and logout
- [x] Gyms, branches and named opening sessions; `X-Gym` tenancy with 404 for other gyms
- [x] Staff: add, edit, deactivate; one role per gym, several branches
- [x] Support access: admin screen to grant and end a read-only window (session 3)

## Members, plans and money
- [x] Plans and offers (admin creates; receptionist applies fixed offers)
- [x] Add a member, notes, set a member's login password, archive (never delete)
- [x] Sell a plan; renewal starts the day after the current plan ends
- [x] Record payments, part payments, never more than owed
- [x] Correct and void payments with a reason (admin only, audited)
- [x] Freeze and unfreeze a membership; cancel a subscription
- [x] Today's collection for the desk

## Attendance
- [x] Front-desk check-in, one per person per local day, expired/frozen turned away
- [x] Wall QR per branch and member/staff self check-in
- [x] Turnstile/biometric punches at `/api/devices/punch/`
- [x] Device API: add, deactivate, rotate token (session 1)
- [x] Devices screen (session 2)
- [x] Attendance by session; members, trainers and receptionists counted apart

## Staff work
- [x] Tasks: assign with due date, start, updates, done, reopen
- [x] Expenses with totals (admin)
- [x] Recurring expenses with due dates, reminders on Home, pay or skip each date
- [x] Payroll: salary rules (fixed, by attendance, hourly, daily), monthly payslips from check-ins, approval,
      part payments, salary history and printable slips
- [x] Admin home summary and reports

## Before the pilot
- [x] Celery + Redis for scheduled jobs; daily reminder list (session 4)
- [x] WhatsApp renewal and dues reminders (session 5)
- [x] CI for API, web and e2e (session 6)
- [x] Deploy setup: API + Postgres on AWS Mumbai, web on Vercel (session 7)
- [x] Backups, restore drill, onboarding a real gym (session 8)

## Rackline billing and WhatsApp
- [x] Rackline admins, the Console, gyms and their admin accounts, suspend and activate (session 9)
- [x] Price list, each gym's Rackline plan, branch quota and buying more branches (session 10)
- [x] Rackline invoices, payments, receipts and what each gym owes (session 11)
- [x] WhatsApp accounts and templates, credentials encrypted (session 12)
- [x] Sending through Meta's Cloud API with templates, no duplicates, retries (session 13)
- [x] Meta webhook: delivery status, STOP replies, shared-number usage (session 14)
- [x] Message switches; automation times set by Rackline admins; payment received, task assigned, Rackline invoice messages (session 15)
- [x] Server status in the Console: health, background jobs, messages and webhook, Run Now (session 16)
- [ ] Message log, usage screens, and end-to-end flows for all of it (session 17)

## Not in the MVP
- Payment gateway (record payments only), check-out or time-in-gym, native apps, more languages.

---

# Sessions

One cloud session per feature, in this order. Start a session with: **"Do session N in ROADMAP.md."**
Each session reads CLAUDE.md (and the api/web CLAUDE.md for its side), does only its task, stops when
"Done when" holds, ticks its line above, and opens a PR. Merge before starting the next one.

## Session 1: Device API
Read `api/CLAUDE.md` and `docs/standards.md`. An API for admins to manage turnstile/biometric devices
(`apps/attendance`, model `Device` exists: branch, name, serial, token, is_active, last_seen).
- `/api/devices/`: list, create, update name/branch, a `deactivate` action. Never delete.
- Admin only; filter by gym; support `?branch=`.
- The token is returned only in the create response. A `rotate-token` action returns a new one.
- Audit create, deactivate and rotate. Regenerate the web client.

**Done when:** `pytest` passes with new `tests/test_devices.py`: admin can create and list; receptionist,
trainer and member are refused; another gym's device answers 404; a deactivated or rotated-out token is refused
at `/api/devices/punch/`; the list stays within a query budget. Don't build the screen.

## Session 2: Devices screen
Read `web/CLAUDE.md` and `docs/design/README.md`. An admin "Devices" screen on the session 1 endpoints.
- Under More (admins only). List per branch: name, serial, active or not, last seen ("Never" if empty).
- "Add Device" task screen (name, serial, branch). After saving, show the token once in a Sheet with a copy
  button and a line saying it won't be shown again.
- On a device: Rename, Rotate Token (confirm), Deactivate (confirm). Loading and empty states.
  Design-system markup only, no new styles.

**Done when:** web typecheck, lint, test and build pass; works at 390 px as meera@rackline.demo; receptionists
don't see it in More.

## Session 3: Support access screen
- API: `SupportAccessViewSet` has create and list only. Add an `end` action (ends = now). Audit grant and end.
- Web: "Support access" under More (admins only): whether a window is open and until when, a "Give Access"
  sheet (2 h, 24 h, 3 days), "End Access" with confirm, and a history list.
- Copy like: "Rackline's team can see your gym, but can't change anything, until 6:00 pm."

**Done when:** `pytest` passes with tests that only admins grant or end, another gym answers 404, support can't
read after the window ends; web checks pass; the flow works at 390 px.

## Session 4: Background jobs
Read `docs/decisions.md`. Add Celery with Redis.
- `config/celery.py`, broker from `CELERY_BROKER_URL` (add to `.env.example`); tasks run eagerly in tests
  and when no broker is set.
- Beat schedule: a daily job per gym at 6:00 gym time (`apps/core/clock.py`) that finds members expiring in
  7, 3 and 0 days and members with a balance due, and writes `ReminderDue` rows (gym, member, kind, for_date;
  unique on all four). Send nothing yet.
- Worker and beat in `docker-compose.yml`; how to run them in `README.md`.

**Done when:** `pytest` passes with tests that the job picks the right members across two gyms in different time
zones, running twice adds no duplicates, archived and frozen members are skipped.

## Session 5: WhatsApp reminders
Read `docs/decisions.md` (Messages). Send renewal and dues reminders from `ReminderDue` rows.
- `apps/messages/`: a sender interface, a `FakeSender` (default; stores what it would send) and a stub for a
  real provider chosen by `WHATSAPP_PROVIDER` (keys in `.env.example`). Call no real API.
- A `Message` record per send (member, kind, status, provider id, error). At most one message per member per
  day. Skip members without a phone or who opted out (new opt-out flag on Member).
- Web (admin): a "Reminders" card on the member profile with recent messages; a gym setting to turn
  reminders on or off.

**Done when:** `pytest` passes covering one-per-day, opt-out, a failed send recorded without stopping the job,
and gym isolation; web checks pass.

## Session 6: CI
`.github/workflows/ci.yml` on push and pull request.
- api: Python 3.12, Postgres 16 service, `pip install -r requirements-dev.txt`, `pytest`.
- web: Node 20, `npm ci`, typecheck, lint, test, build.
- e2e (after both): Postgres + API with `migrate` and `seed_demo`, web running, Playwright chromium,
  `npm run e2e`; upload the Playwright report on failure.
- Cache pip and npm. CI badge in `README.md`.

**Done when:** every job passes on the PR's own run (`gh run list`, `gh run view`).

## Session 7: Deploy setup
Read `docs/decisions.md` (Stack and hosting) and `api/config/settings.py`. Make it ready to deploy; the owner
runs the actual deploy with their AWS and Vercel accounts.
- Production checks (PRODUCTION=true needs SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL, CACHE_URL), static files
  via whitenoise, gunicorn in the Dockerfile, `/api/health/`.
- `docs/deploy.md`: API on AWS ap-south-1 (App Runner or ECS Fargate, RDS Postgres, ElastiCache Redis), Celery
  worker and beat, `web/` on Vercel with `NEXT_PUBLIC_API_URL`, domains, every env var to set.
- A deploy workflow that runs only when started by hand, after CI passes. No real secrets in the repo.

**Done when:** `docker build` of `api/` works; `python manage.py check --deploy` is clean with production env
vars; `/api/health/` has a test; `docs/deploy.md` can be followed without asking.

## Session 8: Backups and pilot readiness
Read `docs/deploy.md`.
- `docs/operations.md`: RDS automated backups (14 days), a monthly restore drill with exact steps, and how
  to check a restored copy.
- `python manage.py verify_counts --gym <slug>`: members, payments and check-ins counts, for the drill.
- Onboarding a real gym is session 9's `create_gym` (the same service as the Console's New Gym).
- Tick everything finished above.

**Done when:** `pytest` passes with a test for verify_counts (it matches seeded data) and the checklist above is
honest.

---

# Rackline billing, WhatsApp and the server (sessions 9–17)

Read `docs/decisions.md` (Roles: Rackline admins; Rackline billing; Messages) first. Rackline's own side lives in
`apps/platform` (gyms, admin accounts) and `apps/billing` (prices, plans, invoices) under `/api/platform/`, with no
`X-Gym`, behind an `IsRacklineAdmin` permission. A gym's own view of its billing stays under `/api/` with `X-Gym`,
admins only. Call the gym's plan with Rackline "Rackline plan" in code and copy: `members.Subscription` is a
member's plan. The Console is a `(console)` route group in `web/`, using the same shell and design system.

## Session 9: Rackline admins and the Console
- API: `IsRacklineAdmin` (`is_superuser` and active). `/api/me/` says `is_rackline_admin`. `AuditLog.gym` may be
  empty (new migration) for changes that belong to no gym.
- `apps/platform`: `services.create_gym` (name, slug, time zone, first branch, owner admin by email: a new login or
  an existing one), and `/api/platform/gyms/`: list (search `q` on name and slug, `?status=`, branch and member
  counts annotated), retrieve, create, update (name, time zone, billing email), `suspend` and `activate` actions
  with a reason. A gym's admins: list, Add Admin, Reset Password, Deactivate (never the owner), Make Owner.
- `python manage.py create_gym` calls the same service.
- Suspended gyms: every gym endpoint answers `RuleBroken("gym_suspended", "This gym's account is paused. Contact
  Rackline to turn it back on.")` with 403, except views marked `open_when_suspended` for admins (`/api/me/` now,
  billing in session 11). The 6 AM job already skips them.
- `seed_demo`: a Rackline admin `rackline@rackline.demo`.
- Web: a Rackline admin lands on `/console`. Gyms list (search, status filter, Load More), a gym's screen (status,
  branches, admins), New Gym task screen, Suspend / Activate with a reason and confirm, the admins list and its
  actions. Gym users of a suspended gym see a "paused" screen (admins can still reach More).

**Done when:** `pytest` passes with new `tests/test_platform.py`: gym admins, desks, trainers, members and
support (`is_staff` without `is_superuser`) are refused `/api/platform/`; create_gym's owner can sign in;
suspended gyms refuse staff and members with `gym_suspended` but let admins reach `/api/me/`; the owner can't be
deactivated; each change is audited; the gyms list keeps a query budget. Web checks pass; the Console works at
390 px as rackline@rackline.demo.

## Session 10: Prices, Rackline plans and branch quota
- `apps/billing`: `PriceList` (base, per branch, WhatsApp setup, machine setup per device, shared message rate per
  category; `active_from`; never edited once in use, a new one is added), `GymBilling` (one per gym: prices copied
  from a price list, `branch_quota`, `billing_day`, `whatsapp_mode` shared | own | off, `paid_until`),
  `BranchRequest` (gym, how many, asked by, status asked | approved | declined, decided by and when).
- `create_gym` gives the new gym a `GymBilling` from the current price list (quota 1). A data migration gives
  existing gyms one, with the quota set to their active branches.
- Quota rule in a service, under `select_for_update` on the gym's `GymBilling`: creating a branch or turning
  `is_active` back on past the quota raises `RuleBroken("branch_limit", ...)` (copy in decisions.md). Lowering a
  quota below the active branches is refused.
- Console: Prices (current list, Add Price List), a gym's Rackline plan (prices, quota, billing day, WhatsApp mode,
  Move to Current Prices), branch requests to Approve or Decline. Approving raises the quota at once and records
  the pro-rata amount for session 11 to bill.
- Gym admin: More → Rackline plan (prices, quota, branches in use) with Add Branch to My Plan; Branches shows
  "2 of 3 branches" and explains the limit when it's reached.

**Done when:** `pytest` passes with new `tests/test_billing.py`: a branch past the quota is refused on create and
on reactivate (a two-connection `transaction=True` test for two at once), a request approved raises the quota and
works out the pro-rata amount (month ends, 28/30/31-day months), gym admins can't approve their own, another gym's
request answers 404, changes are audited. Web checks pass at 390 px.

## Session 11: Rackline invoices and payments
- `Invoice` (gym, number per financial year `RL/2026-27/0001`, period, status open | paid | void, totals with tax
  fields at zero), `InvoiceLine` (base | branches | branches_pro_rata | whatsapp_usage | whatsapp_setup |
  machine_setup | adjustment; quantity, rate, amount, tax), `InvoicePayment` (amount, method, reference, date,
  void reason). One-time setup charges are added by a Rackline admin as pending lines for the next invoice.
- A daily beat job writes each gym's invoice on its billing day: the month ahead, pro-rata branches and pending
  lines; WhatsApp usage joins once session 14 counts it (leave the hook). Safe to run twice (unique on gym and
  period). Paying an invoice in full moves `paid_until`.
- Console: a gym's invoices and payments, Record Payment (part payments, never more than owed, under a lock), Void
  Invoice and Void Payment with a reason, Add Charge, what every gym owes on the gyms list.
- Gym admin (open when suspended): More → Rackline plan shows invoices, what's owed, and each receipt with a print
  page like the salary slip.

**Done when:** `pytest` passes: the job is safe to repeat and right across month ends and a financial year's
first invoice, payments never exceed what's owed (race test), voids keep history, invoice numbers never repeat,
admins of a suspended gym can read their invoices, desks and other gyms can't. Web checks pass at 390 px.

## Session 12: WhatsApp accounts and templates
- Add `cryptography`; `FIELD_ENCRYPTION_KEY` (comma-separated keys, MultiFernet, so the key can be rotated) in
  settings, `.env.example` and `docs/deploy.md`. Production refuses to start without it.
- `apps/messages`: `WhatsAppAccount` (gym, or none for Rackline's shared number; WABA id, phone number id, display
  number, access token and app secret encrypted, `webhook_slug`, verify token, status) and `WhatsAppTemplate`
  (account, message kind, Meta name, language, category, the parameter list in order, status). Kinds:
  `plan_ending`, `plan_ends_today`, `payment_due`, `payment_received`, `task_assigned`, `rackline_invoice_due`,
  `rackline_payment_received`.
- Console: accounts (Add Account, Replace Credentials, Test Connection, which only asks Meta for the number's
  details), and each account's templates. Credentials are write-only: responses show the last 4 characters only.
- Gym admin: More → Settings → WhatsApp shows the mode, the number and whether it is working.
- The current `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_ID` env vars go: the shared number is an account row.

**Done when:** `pytest` passes: no response, log line or audit row contains a credential, only Rackline admins
change accounts or templates, a gym's admins see their own account only, encryption round-trips and survives a
key rotation. Web checks pass.

## Session 13: Sending through Meta
- `CloudSender` posts templates to `https://graph.facebook.com/<WHATSAPP_API_VERSION>/<phone_number_id>/messages`
  with the account's token (`to` without the `+`). It picks the gym's own account or the shared one from
  `whatsapp_mode`. `FakeSender` stays the default and for tests; tests mock the HTTP call.
- `Message` grows (new migration, existing rows backfilled): account, template, parameters, recipient (a member or
  a user), `dedupe_key` unique per gym (replaces `one_message_per_member_per_day`; a reminder's key is
  `member:<id>:reminder:<date>`, which keeps one a day), status queued | sent | delivered | read | failed, attempts,
  `next_retry_at`, error code, `billable` and `rate_paise` (shared number only, rate from the gym's plan).
- Write the row as queued, then send, then save Meta's id. Temporary Meta errors retry up to 3 times with growing
  waits (a Celery task); others fail at once. The words for the record come from the template's text.
- The member reminders move onto templates; existing `test_messages.py` keeps passing.

**Done when:** `pytest` passes: the payload matches Meta's template shape, own vs shared account is chosen right,
a crash after the row is written never sends twice, retries stop at 3 and skip permanent errors, a gym that is
suspended or in mode off sends nothing.

## Session 14: Meta webhook and usage
- `/api/whatsapp/webhook/` (shared) and `/api/whatsapp/webhook/<slug>/` (a gym's own account): GET verification
  with the verify token, POST checked against `X-Hub-Signature-256` with the account's app secret, raw event
  stored (`WebhookEvent`) before processing, always 200 to Meta once the signature checks.
- Status updates find the message by Meta's id **within the account that sent it**, move sent → delivered → read,
  never back; failed keeps Meta's code and reason. Times from Meta are UTC.
- Incoming messages are stored (`InboundMessage`, unique on Meta's id); a member replying STOP is opted out.
- Usage: delivered billable messages on the shared number per gym per month (counted, never a running counter).
  Session 11's invoice job adds last month's usage line.

**Done when:** `pytest` passes: a bad or missing signature is refused, the verification handshake works, a status
for another account's message changes nothing, a repeated "delivered" counts once, an out-of-order "delivered"
after "read" is ignored, STOP opts out, usage on an invoice matches the delivered messages.

## Session 15: Message switches, automation times and new messages
- Automation times are Rackline's (decisions.md, Messages): `AutomationSchedule`, one Rackline-wide row: the
  reminders' hour (default 6, gym time), days ahead (default 7 and 3) and the invoice job's hour on a billing day
  (default 0, the first run after the gym's midnight). Whole hours only.
- `NotificationRule` per gym and message kind: on or paused (the gym's admins), and for scheduled ones an hour and
  days ahead that override the Rackline-wide ones for that gym (Rackline admins only; empty means Rackline's). A
  data migration carries `reminders_on` over, then the field goes; `REMINDER_HOUR` goes too. Member receipts start
  off; the rest on.
- Beat keeps ticking as now (reminders every 15 minutes, invoices hourly); each tick reads the times from the
  database, so a change takes effect on the next tick without restarting anything.
- Payment received: sent after a payment is recorded (after the transaction commits), not for a void. Task
  assigned: sent to the staff member when an admin assigns a task. Rackline invoice due (before and after the due
  day) and Rackline payment received go to the gym's owner from Rackline's shared number, set by Rackline admins.
- Console: Automation (the Rackline-wide times), and on a gym's screen its message times with Use Rackline's Times
  to clear an override. Every change is audited.
- Gym admin: More → Settings → Messages, a switch per message (Pause / Resume), and when each one goes out,
  read-only ("Set by Rackline"); replaces the reminders switch.

**Done when:** `pytest` passes: each switch stops its message and only its message; a gym's admins can pause and
resume but the API refuses them a time or days ahead; only Rackline admins change times, Rackline-wide and per gym,
audited; a gym's override beats the Rackline-wide time and clearing it goes back; times follow the gym's time zone
and a change applies on the next tick; a payment's receipt and a task's message go once; the owner messages respect
the invoice dates. Web checks pass at 390 px.

## Session 16: Server status
- `JobRun` (job, started and finished, what it did as counts, the error if it failed), written by every scheduled
  job: reminders, invoices, retries and the webhook replay. Runs that did nothing are kept only as each job's latest
  tick; the rest for 30 days, pruned by the jobs themselves.
- `/api/platform/status/` (Rackline admins only, no `X-Gym`): the API's version and deploy time (`APP_VERSION`,
  `DEPLOYED_AT` from the deploy, in `.env.example` and `docs/deploy.md`); the database and Redis reachable; the
  Celery worker answering a ping (2-second limit); beat's last tick; each job's last run, how long it took and what
  it did; messages waiting for a retry and failed today; webhook calls that couldn't be handled in the last 7 days
  and Meta's last call to each number. Anything down shows as down, never a 500.
- Run Now (`/api/platform/jobs/<job>/run/`): reminders, invoices, and the webhook replay of the last 7 days' failed
  calls. The same safe-to-repeat jobs, queued on the worker rather than run in the request, refused while that job
  is running, audited.
- `/api/health/` stays as it is for the load balancer: it says no more than it does now.
- Console → Server: health, the jobs with their last run and Run Now (with a confirm), and messages and webhook.

**Done when:** `pytest` passes: only Rackline admins reach the status and Run Now (gym admins, desks, trainers,
members and support refused); a dead database, Redis or worker shows as down; Run Now queues once, is refused while
the job runs, and is audited; every job writes its run; the status keeps a query budget. Web checks pass at 390 px.

## Session 17: Message log, usage and end-to-end
- `/api/messages/` gains filters (status, kind, recipient, from/to dates) and a Retry action for a failed message
  (admins; same dedupe key, so never twice). Console: usage per gym per month on the shared number. (The Console's
  message log across gyms is in: `/api/platform/messages/`, Console → More → WhatsApp log.)
- Gym admin: More → Messages, the log with Load More and filters, and this month's usage on the shared number.
- `e2e/flows.spec.ts`: Rackline admin creates a gym, sets its quota, approves a branch request, records a payment;
  a gym admin hits the branch limit, sees the invoice and receipt; a suspended gym's desk sees the paused screen;
  a Rackline admin changes a gym's reminder time and opens Server.

**Done when:** every check in the root `CLAUDE.md` passes, including `npm run e2e`, and every box above is ticked.
