# Rackline

Gym management for many gyms: members, plans and payments, check-ins (desk, wall QR, turnstile), staff and tasks.

```
rackline/
  api/   Django + DRF backend
  web/   Next.js PWA: the app every role uses (see web/README.md)
```

Product and architecture decisions are in `docs/decisions.md`; the design system (colours, type, voice,
every component's rules and markup) is in `docs/design/`. `CLAUDE.md` files brief Claude Code on the project.

## Run the API on your machine (Windows)

You need Python 3.12+ and either Docker Desktop or a local PostgreSQL 16.

```powershell
cd D:\dev\freelance-projects\rackline
docker compose up -d                     # Postgres + Redis

cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo               # the demo gym from the prototype
python manage.py runserver
```

Open http://localhost:8000/api/docs/ for every endpoint. To try one there: call `POST /api/auth/login/`,
press **Authorize** and paste the `access` token, and send the header `X-Gym: rackline-fitness`.

No Docker? Remove the `DATABASE_URL` line from `.env` and the API uses a local SQLite file instead.

Tests: `pytest` (in `api/`).

### Demo logins (password `rackline-demo`)

| Who | Sign in with | Role |
|---|---|---|
| Meera Iyer | meera@rackline.demo | Admin, account owner |
| Arjun Rao | arjun@rackline.demo | Receptionist · Indiranagar, Koramangala |
| Kavya Nair | kavya@rackline.demo | Receptionist · HSR Layout, Whitefield |
| Neha Sharma | neha@rackline.demo | Trainer · Indiranagar |
| Neeraj, Alex, Imran | neeraj@ / alex@ / imran@rackline.demo | Trainers |
| Aarav Reddy | 9800000001 | Member (first 10 members have logins) |

`python manage.py seed_demo --reset` rebuilds the demo gym.

## How the API works

- **Sign in:** `POST /api/auth/login/` with `identifier` (staff email, or a member's 10-digit mobile) and `password`.
  Send `Authorization: Bearer <access>`. Refresh at `/api/auth/refresh/`. `GET /api/me/` lists the gyms and branches you can open.
- **One gym per request:** send `X-Gym: <slug>`. A gym you have no role in answers 404, as if it didn't exist.
- **Roles:** admin (everything, every branch), receptionist (desk work in their branches, today's collection, fixed
  offers only), trainer (their own members' status and phone, "payment due" without amounts; their tasks),
  member (themselves). Rackline support can only read, and only inside a window an admin grants (`/api/support-access/`).
- **Money** is whole paise (`150000` = ₹1,500). **Times** are stored in UTC and worked out in the gym's time zone.
- **Errors** always look like `{"error": {"code": "...", "message": "...", "fields": {...}}}`. Business rules answer
  409 with a code the app can act on: `membership_expired`, `membership_frozen`, `already_checked_in`, `overpaid`,
  `offer_not_valid`, `wrong_branch`...
- **Nothing important is deleted:** payments are voided, staff deactivated, members archived. Corrections, voids,
  freezes and role changes go to the audit log.

### Endpoints

| Area | Endpoints |
|---|---|
| Branches | `/api/branches/` with opening sessions (Morning 5–10, Evening 5–10...) sent as one list |
| Staff | `/api/staff/` (creates the login), `/api/support-access/` |
| Plans and offers | `/api/plans/`, `/api/offers/?current=1` |
| Members | `/api/members/?q=&status=&branch=`, `.../notes/`, `.../set-login/`, `.../history/` |
| Selling | `/api/subscriptions/` (renewals start after the current plan), `.../freeze/`, `.../unfreeze/`, `.../cancel/` |
| Payments | `/api/payments/`, `.../void/`, `/api/payments/collection/?date=` |
| Check-in | `/api/checkins/?date=&branch=&kind=member\|trainer\|receptionist&session=Morning`, `/api/checkins/summary/`, `/api/checkins/qr/`, `/api/devices/punch/` |
| Tasks | `/api/tasks/`, `.../start/`, `.../updates/`, `.../done/`, `.../reopen/` |
| Expenses | `/api/expenses/?month=2026-10`, `/api/expenses/totals/` |
| Home | `/api/reports/summary/?date=&branch=` |

### Check-in rules

One check-in per person per day; only the time in is recorded (no check-out). Expired or frozen plans are turned
away. Staff can only check in at branches they work at. A check-in belongs to the session it falls in; during a break
it counts toward the next session. Turnstiles (ZKTeco/eSSL) post punches to `/api/devices/punch/` with their
`X-Device-Token` and get back `{"open": true|false}`; the vendor adapter that translates their push format comes later.

## Run the web app

With the API running, in a second terminal:

```powershell
cd D:\dev\freelance-projects\rackline\web
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000 and sign in with a demo login. Details in `web/README.md`.

## Next steps

1. WhatsApp renewal reminders (Celery + Redis, Rackline's number first).
2. Turnstile vendor adapter (ZKTeco/eSSL push format), then the pilot at the current client from week 9.
3. Password reset by the desk for staff, and members changing their own password.
