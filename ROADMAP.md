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
- [x] Admin home summary and reports

## Before the pilot
- [x] Celery + Redis for scheduled jobs; daily reminder list (session 4)
- [x] WhatsApp renewal and dues reminders (session 5)
- [x] CI for API, web and e2e (session 6)
- [ ] Deploy setup: API + Postgres on AWS Mumbai, web on Vercel (session 7)
- [ ] Backups, restore drill, onboarding a real gym (session 8)

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
- `python manage.py create_gym`: a real gym (name, slug, time zone, first branch, owner admin by email).
- Tick everything finished above.

**Done when:** `pytest` passes with tests for both commands (create_gym's owner can sign in; verify_counts
matches seeded data) and the checklist above is honest.
