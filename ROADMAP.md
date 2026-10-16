# Roadmap (MVP)

Tick a box when the API, the screen and a test are all in. Decisions behind each item: `docs/decisions.md`.

## Accounts and gyms
- [x] Sign in by email (staff) or phone (member), JWT with refresh and logout
- [x] Gyms, branches and named opening sessions; `X-Gym` tenancy with 404 for other gyms
- [x] Staff: add, edit, deactivate; one role per gym, several branches
- [ ] Support access: admin screen to grant and end a read-only window (API done, no screen)

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
- [ ] Device screen: register a device, see its key and last punch (today only in Django admin)
- [x] Attendance by session; members, trainers and receptionists counted apart

## Staff work
- [x] Tasks: assign with due date, start, updates, done, reopen
- [x] Expenses with totals (admin)
- [x] Admin home summary and reports

## Before the pilot
- [ ] WhatsApp renewal and dues reminders (from Rackline's number)
- [ ] Celery + Redis for scheduled jobs (reminders, expiring-plan sweeps)
- [ ] Deploy: API + Postgres on AWS Mumbai, web on Amplify or Vercel
- [ ] Backups and restore drill for the database
- [ ] e2e flows green in CI for each role

## Not in the MVP
- Payment gateway (record payments only), check-out or time-in-gym, native apps, more languages.
