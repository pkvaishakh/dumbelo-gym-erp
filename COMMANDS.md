# Commands

PowerShell, from the repo root. Demo password: `rackline-demo`.

## First time

```powershell
docker compose up -d
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo
cd ..\web
npm install
npx playwright install chromium
```

## Start

```powershell
docker compose up -d                                                  # Postgres + Redis
cd api; .venv\Scripts\activate; python manage.py runserver            # http://localhost:8000/api/docs/
cd web; npm run dev                                                   # http://localhost:3000
```

Background jobs (optional; set `CELERY_BROKER_URL=redis://localhost:6379/0` in `api/.env`):

```powershell
cd api; .venv\Scripts\activate; celery -A config worker --loglevel=info
cd api; .venv\Scripts\activate; celery -A config beat --loglevel=info
docker compose up -d worker beat                                      # or both in Docker
```

## Rackline admin (super admin, the Console)

```powershell
cd api; .venv\Scripts\activate
python manage.py createsuperuser                                      # asks email, name, password
```

Make an existing login a Rackline admin:

```powershell
python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(email='you@example.com').update(is_superuser=True, is_staff=True)"
```

## Gyms

```powershell
python manage.py create_gym --name "Pulse Fitness" --slug pulse --branch Kochi --owner-email anil@pulse.in --owner-name "Anil Menon" --owner-password "first-pass-123"
python manage.py seed_demo --reset                                    # rebuild the demo gym
```

## Database

```powershell
python manage.py migrate
python manage.py makemigrations
python manage.py verify_counts --gym pulse --until 2026-10-19T03:30Z  # restore drill
```

## After changing an endpoint or serializer

```powershell
cd api; python manage.py spectacular --file ../web/openapi.yml
cd ..\web; npm run api
```

## Jobs by hand

```powershell
python manage.py write_invoices                                       # today's billing day
python manage.py write_invoices --day 2026-11-01                      # a missed day
python manage.py replay_webhook_events --failed
python manage.py replay_webhook_events --since 2026-10-18T00:00Z
python manage.py rotate_credentials                                   # after a new FIELD_ENCRYPTION_KEY
```

## Checks

```powershell
cd api; pytest
cd web; npm run typecheck; npm run lint; npm run test; npm run build
cd web; npm run e2e                                                   # API running, demo gym fresh (seed_demo --reset)
```

Don't `npm run build` while `npm run dev` is running: stop it first.

## Before a release

```powershell
cd api; python manage.py check --deploy; pip install pip-audit; pip-audit
cd web; npm audit
```
