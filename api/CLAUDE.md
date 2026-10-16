# Rackline API (Django 5.1 + DRF)

## Layout

```
config/              settings (django-environ, .env), urls (router + a few APIViews)
apps/core/           tenancy.py (X-Gym, InGym permission, role tuples, GymViewMixin), errors.py (RuleBroken,
                     error shape), clock.py (gym time zone, days, months), money.py, models.py (GymScoped base),
                     management/commands/seed_demo.py
apps/accounts/       User (email for staff, +91 phone for members), login/refresh/me
apps/gyms/           Gym, Branch, BranchSession (named opening hours), GymRole (one role per user per gym,
                     branches M2M, is_owner), SupportAccess
apps/members/        Plan, Offer, Member, MemberNote, Subscription, Payment; services.py (sell, take_payment)
apps/attendance/     CheckIn (member XOR staff), Device; services.py (check_in: the one rule book)
apps/tasks/          Task, TaskUpdate (note | status)
apps/expenses/       Expense
apps/reminders/      ReminderDue + the daily job that fills it (services.py, tasks.py); Celery in config/celery.py
apps/reports/        SummaryView (admin home)
apps/audit/          AuditLog + record(request, action, obj, before, after)
tests/               pytest; conftest.World builds a small gym (two branches, admin, desks, trainer, member)
```

## How to add an endpoint

1. Business rules go in the app's `services.py`, not in views or serializers. Raise `RuleBroken("code", "message")`.
2. Views subclass `GymViewMixin` and declare roles per action:
   `roles = {"list": STAFF, "retrieve": STAFF, "*": ADMIN}` (tuples in `apps/core/tenancy.py`).
3. `get_queryset` always starts from `Model.objects.filter(gym=self.gym)` and uses
   `self.in_my_branches(qs, "branch")` for branch-scoped data. Admins get every branch (`branch_ids()` is None).
4. Serializers that take foreign keys must only accept rows from the caller's gym (see `GymPK` in
   `apps/members/serializers.py`).
5. Audit anything that changes money, access or history: `record(self.request, "thing.done", obj, before, after)`.
6. Add `@extend_schema` for actions so the OpenAPI schema (and the web's generated client) stays typed.
7. Test it in `tests/` with the `w` fixture, including another gym (`other` fixture) to prove isolation and a
   role that must be refused. Lists also get a query budget (`django_assert_max_num_queries`) so an N+1 fails.

Full rules (query patterns, pagination, filters, throttling, review order): `../docs/standards.md`.

## Conventions

- Money fields end in `_paise` and are integers. Dates the user sees are local (`clock.today(gym)`).
- Member status is computed (`Member.status()`): active, expiring (≤7 days), due (balance > 0), frozen, expired, none.
- A renewal starts the day after the current plan ends (`services.next_start`). Freezing moves the end date.
- A check-in's session is the one its time falls in; during a break it counts toward the next session.
- Keep docstrings short and in plain words; the error and help texts are user-facing.
- Lists of members load through `Member.objects.with_totals()` (balance, status and current plan without a query
  per row); subscriptions through `.with_paid()`. Ids read from query params go through `int_param`.
- Settings come from `.env` (copy `.env.example`). No DATABASE_URL means SQLite. Servers set `PRODUCTION=true`.
