# Dumbelo

Gym management SaaS for Indian gyms: many gyms (tenants), each with branches, staff and members.
Members, plans, offers and payments, check-ins (front desk, wall QR, turnstile), staff tasks, expenses.
Phone-first web app (PWA) used by four roles: admin, receptionist, trainer, member.

```
api/    Django 5 + DRF + Postgres backend          → api/CLAUDE.md
web/    Next.js 15 PWA, the app every role uses     → web/CLAUDE.md
docs/   decisions.md (product and architecture decisions), deploy.md (AWS + Vercel), operations.md (backups, the
        restore drill, opening a gym), design/ (design system)
```

Read `docs/decisions.md` before changing behaviour, and `docs/design/README.md` before changing any screen.
Every change follows `docs/standards.md` (architecture, reuse, queries, security, tests, review order).

## Run it (Windows, from the repo root)

```powershell
docker compose up -d                          # Postgres + Redis (or skip: the API falls back to SQLite)
cd api; .venv\Scripts\activate; python manage.py runserver      # http://localhost:8000/api/docs/
cd web; npm run dev                                              # http://localhost:3000
```
First time: see README.md (venv, `pip install -r requirements-dev.txt`, `migrate`, `seed_demo`, `npm install`).
Demo logins, password `dumbelo-demo`: meera@ (admin), arjun@ / kavya@ (receptionists), neha@ (trainer)
`@dumbelo.demo`, member `9800000001`, Dumbelo admin (the Console) dumbelo@. `python manage.py seed_demo --reset` rebuilds the demo gym.

## The four roles (one role per person per gym; full rules in `docs/decisions.md`)

| Role | Can | Can't |
|---|---|---|
| Admin | Everything in every branch: plans, offers, staff, branches, reports, expenses, recurring bills, payroll, cash and bank, correct/void payments, refunds, settle cash counts, reconcile, tasks | Remove the account owner |
| Receptionist | In their branches: add members, sell plans, record payments, apply fixed offers, check people in, payments and expenses one day at a time (and add expenses), their branches' cash in hand (read-only) and counting it at close, their tasks | Revenue totals, reports, staff data, the bank, expenses over longer spans, edit expenses, make offers, correct/void, refunds, move money, settle a count |
| Trainer | Their own members' status and phone, "payment due" (no amount), their tasks, check in | See any amount |
| Member | Their own membership and visits, self check-in by wall QR | See anyone else |

Dumbelo support: read-only, only while an admin-granted window is open, and logged.
Dumbelo admins (`is_superuser`): the Console (`/console`, `/api/platform/`): gyms, their admins, prices, Dumbelo
invoices, WhatsApp accounts, when automation runs (gym admins only pause and resume messages), server status.
Never a gym's members or money without a support window.

## Don't touch

- `web/src/api/gen/` and `web/openapi.yml`: generated. Regenerate (command below), never hand-edit.
- `web/src/styles/` (tokens.css, dumbelo.css): the design system. No new colours, fonts, shadows or radii.
- Existing migrations: add a new one, never edit or delete an applied one.
- `.env` files: never commit them; change `.env.example` instead.
- `ROADMAP.md` scope: don't build what it marks "not in MVP" (payment gateway, check-out, native apps) unless asked.
- No hard deletes of members, payments, staff or plans; no floats for money; no check-out field anywhere.

## Cloud sessions (Linux)

`scripts/cloud-setup.sh` runs at session start (hook in `.claude/settings.json`): it makes `api/.venv`, writes
`api/.env` without `DATABASE_URL` (so SQLite), migrates, seeds the demo gym and runs `npm ci` in `web/`.
Use Linux syntax there: `cd api && pytest`, `cd web && npm run typecheck && npm run lint && npm run test`.
The venv is already on `PATH`. To run the app: `cd api && python manage.py runserver &` and `cd web && npm run dev &`.

## Checks before you say something is done

- API: `cd api; pytest`
- Web: `cd web; npm run typecheck; npm run lint; npm run test; npm run build`
- Flows: `cd web; npm run e2e` (API running with the demo gym)
- After changing an API endpoint or serializer: regenerate the web client
  `cd api; python manage.py spectacular --file ../web/openapi.yml; cd ../web; npm run api`

## Rules that hold everywhere

- **Tenancy**: every request inside a gym carries `X-Gym: <slug>`. Every gym-owned query filters by the gym, and
  by the caller's branches where branches matter. A gym you have no role in answers 404, never 403.
- **Roles are enforced by the API.** The web hides what a role can't use, but security lives in `roles = {...}`
  on each view. Trainers never see payment amounts; receptionists only their branches and fixed offers;
  members only themselves; Dumbelo support is read-only and only inside a window an admin grants.
- **Money is integer paise** (`150000` = ₹1,500), shown with Indian grouping (`₹1,50,000`). Never floats.
- **Time**: stored UTC, worked out in the gym's time zone (`apps/core/clock.py`). One check-in per person per
  local day. **Check-in time only: no check-out anywhere.**
- **Nothing important is deleted**: payments are voided, staff deactivated, members archived, plans taken off
  sale. Corrections, voids, freezes and role changes are written to the audit log.
- **Errors** are `{"error": {"code", "message", "fields"?}}`. Business rules raise `RuleBroken(code, message)`
  (409); the message is shown to the user as is, so write it for them ("Renew it to check in").
- **Copy**: plain, second person, no jargon ("gym", "members", never "tenant" or "ERP"). Action labels in
  Title Case ("Collect Payment"), everything else sentence case. Full voice guide in `docs/design/README.md`.
