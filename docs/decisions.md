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
  checks people in, adds members and sells plans. No revenue totals, reports, staff data or expenses.
- Trainer: their own members' status and phone, and "payment due" without amounts. Their tasks.
- Member: their own membership, visits, and self check-in.
- Rackline support sees a gym only with the gym's time-limited permission (read-only, logged).

## Money
- Record payments only (no payment gateway in the MVP). Part payments allowed; never more than what's owed.
- Discounts only through offers (percent or amount off, date range, optional plans). Admins correct or void
  payments, with a reason, audited. Nothing is deleted.

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
