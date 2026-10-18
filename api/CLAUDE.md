# Rackline API (Django 5.1 + DRF)

## Layout

```
config/              settings (django-environ, .env), env.py (what a server must be told with
                     PRODUCTION=true), urls (router + a few APIViews)
apps/core/           tenancy.py (X-Gym, InGym permission, role tuples, GymViewMixin, suspended gyms: gym_suspended and
                     `open_when_suspended`), rackline.py (IsRacklineAdmin, RacklineViewMixin), errors.py (RuleBroken,
                     error shape), clock.py (gym time zone, days, months), money.py, models.py (GymScoped base), queries.py (count_of, sum_of: a per-row COUNT or SUM subquery),
                     views.py (/api/health/), middleware.py (lets the load balancer's check through),
                     management/commands/seed_demo.py
apps/accounts/       User (email for staff, +91 phone for members), login/refresh/me
apps/gyms/           Gym, Branch, BranchSession (named opening hours), GymRole (one role per user per gym,
                     branches M2M, is_owner), SupportAccess
apps/members/        Plan, Offer, Member, MemberNote, Subscription, Payment, Refund; services.py (sell, take_payment, refund,
                     void_refund); views/ (members.py, refunds.py)
apps/attendance/     CheckIn (member XOR staff), Device; services.py (check_in: the one rule book)
apps/tasks/          Task, TaskUpdate (note | status)
apps/expenses/       Expense, RecurringExpense + ExpenseDue (each date a bill is due); services.py (sync_dues,
                     pay_due, skip_due, bills_due)
apps/payroll/        SalaryRule (+ SalaryItem), Payslip (+ PayslipLine), SalaryPayment; services.py (generate,
                     pay_for, approve, pay, salaries_owed). Paying a bill or salary writes an Expense
apps/finance/        Account (branch cash or bank; BranchAccount: the one bank account a branch uses), MoneyMove (deposit,
                     withdrawal, transfer), DrawerClose (the desk's cash count), Reconciliation + StatementTick (bank
                     reconciliation); services.py (with_balance, set_branches, move, void, overview, statement, close_drawer,
                     settle_close, cash_today, before_change), reconcile.py (tick, reconcile, unreconcile). Payments, refunds
                     and expenses carry the account they hit: `Account.objects.for_money(branch_id, method, on=day)`, called
                     inside the transaction that records them. Anything that corrects, voids or removes one calls
                     `before_change(kind, id)` first (reconciled entries are locked)
apps/reminders/      ReminderDue + the rules that fill it (services.py, tasks.py); Celery in config/celery.py
apps/messages/       WhatsApp: senders.py (FakeSender by default; CloudSender posts templates to Meta), Message (queued |
                     sent | delivered | read | failed, `dedupe_key` unique per gym), services.py (Route: the number and
                     templates a gym sends from; queue → deliver → keep Meta's id; send_due: the reminders;
                     send_retries: temporary failures, 3 retries), and the 6 AM job and the retry sweep (tasks.py). WhatsAppAccount (Rackline's shared number has no gym; a gym's own)
                     and WhatsAppTemplate (kinds and their PARAMETERS); crypto.py (EncryptedTextField over
                     FIELD_ENCRYPTION_KEY, MultiFernet; `manage.py rotate_credentials`); accounts.py (add_account,
                     change_account, replace_credentials, test_connection, account_for: the account a gym sends from,
                     save_template, approved_templates); meta.py (Graph API calls, errors scrubbed of credentials and sorted into
                     temporary, permanent and "no answer", which is never retried); views/gym.py
                     (/api/messages/, /api/gym/whatsapp/) and views/console.py (/api/platform/whatsapp-accounts/,
                     /api/platform/whatsapp-templates/). Querysets that show an account defer SECRET_FIELDS.
                     App label "gym_messages": see apps.py
apps/reports/        views/summary.py (SummaryView: admin Home, including expense dues; writes due dates); one read-only
                     report per category (views/overview, revenue, expenses, money, members, attendance, tasks:
                     GET /api/reports/<category>/?from&to&branch), sharing period.py (report_range: at most MAX_MONTHS = 3
                     calendar months, never after the gym's today; Period: the querysets, `compare` with the days before
                     in one query, `daily`) and serializers.py (typed response shapes)
apps/platform/       Rackline's side under /api/platform/ (no X-Gym, Rackline admins only): services.py (create_gym, suspend,
                     activate, add_admin, reset_admin_password, deactivate_admin, make_owner), views.py (gyms, a gym's admins),
                     management/commands/create_gym.py (the same service)
apps/billing/        A gym's Rackline plan: PriceList (never edited), GymBilling (prices copied from a list, branch_quota,
                     billing_day, whatsapp_mode, paid_until), BranchRequest (asked | approved | declined, with the pro-rata
                     charge); services.py (open_plan, change_plan, move_to_current_prices, make_room_for_branch: call it in
                     the transaction that opens or reopens a branch, ask_for_branches, approve (writes the pending
                     pro-rata line), decline, pro_rata, locked_plan: lock this first for anything that changes what a
                     gym owes); views/gym.py (/api/billing/plan/, open when suspended; /api/billing/branch-requests/) and
                     views/console.py (/api/platform/prices/, /api/platform/gyms/<id>/plan/, /api/platform/branch-requests/).
                     Invoices: Invoice (open | paid | void, tax fields at zero), InvoiceLine (no invoice yet = pending),
                     InvoicePayment (receipt, voided with a reason), NumberSeries (RL/2026-27/0001 under a lock);
                     invoicing.py (write_invoice, gyms_billed_on, whatsapp_usage_lines: the hook session 14 fills,
                     add_charge, remove_charge, record_payment, void_payment, void_invoice, owed_by_gym); tasks.py
                     (write_invoices: beat, hourly; `manage.py write_invoices --day` for a missed day); views/gym.py
                     (/api/billing/invoices/, open when suspended) and views/invoices.py (/api/platform/invoices/,
                     /api/platform/invoice-payments/, /api/platform/charges/)
apps/audit/          AuditLog + record(request, action, obj, before, after, gym=None): pass `gym` from the Console
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
