# Coding standards

How we write Rackline code. These rules apply to every change. A change that breaks one doesn't get merged, unless it
writes the exception down next to the code (the way `MemberViewSet.list` explains its status filter).

This page holds the rules. The how-to lives in the guides it points to:
`CLAUDE.md` (rules everywhere), `api/CLAUDE.md` (adding an endpoint), `web/CLAUDE.md` (building a screen),
`docs/decisions.md` (product decisions), `docs/design/README.md` (design system and voice).

## 1. Architecture: where code goes

Each layer has one job. Keep code in the layer that owns it.

| Layer | Owns | Never |
|---|---|---|
| `models.py` | Fields, constraints (`UniqueConstraint`, `CheckConstraint`), small helpers about one row | Requests, roles, HTTP |
| `services.py` | Business rules and multi-step writes, in `transaction.atomic`; raises `RuleBroken` | Reading `request`, building responses |
| `serializers.py` | Input validation and output shape; foreign keys via `GymPK` | Business rules, per-row queries |
| `views.py` | Roles, the scoped queryset, filters, wiring a serializer to a service, audit | Business rules, money maths |
| `apps/core/` | Code used by two or more apps: tenancy, clock, money, errors | Code only one app needs |

- **One app per business area** (`members`, `attendance`, `tasks`…). An app imports from `core` and from apps it
  depends on. It never imports from `reports`. Circular imports mean the code is in the wrong app.
- **Split a file into a package before it reaches about 400 lines**, e.g. `apps/members/views/payments.py`. Don't
  create `utils.py` grab bags. Name the module after what it does.
- **Web**: a route's `page.tsx` composes the screen. Anything two routes use goes in `src/features/`. Design-system
  pieces go in `src/components/`. Logic without UI goes in `src/lib/`. Split a page once it passes about 250 lines.

## 2. No duplication

Search before you write. If the thing exists, use it. If it nearly exists, extend it.

- **Single sources** to reuse, never re-implement:
  - Gym, role and branch scoping: `GymViewMixin`, `in_my_branches`, role tuples (`apps/core/tenancy.py`)
  - Rackline's own views (`/api/platform/`): `RacklineViewMixin` / `IsRacklineAdmin` (`apps/core/rackline.py`)
  - Foreign key input: `GymPK` (`apps/members/serializers.py`)
  - Times, days and local formatting: `apps/core/clock.py`
  - Paise and rupees: `apps/core/money.py` (API), `src/lib/format.ts` (web)
  - Errors: `RuleBroken` (API), `ApiError` + `fieldError` (web)
  - Business rules: `members/services.py` (sell, take_payment), `attendance/services.py` (check_in)
  - Calling the API: the generated hooks in `src/api/gen/`, then `useGet`/`useAction`. Never call `fetch` directly.
  - UI: `src/components/ui.tsx`, `shell.tsx`, `src/features/*`
- **Constants live once.** Member statuses, payment methods and roles are defined in one place (model choices or
  `core`) and imported everywhere else. The web gets them from the generated enums.
- **Logic used twice becomes a function the second time.** Don't wait for the third. Example: counting check-ins by
  session is needed by both the Home summary and the Attendance summary, so it belongs in `attendance/services.py`.

## 3. Performance

### Queries
- **A list endpoint runs a fixed number of queries, whatever the page size.** Every list endpoint has a test that
  pins this with `django_assert_max_num_queries` (see §7).
- **Serializers never query per row.** No `SerializerMethodField` that calls `.filter()`, `.aggregate()`, `.count()`
  or a model method that does. Per-row values come from the queryset:
  - related rows: `select_related` (foreign keys) or `prefetch_related` / `Prefetch(..., to_attr=...)` (reverse and
    many-to-many)
  - computed values: `annotate()` with `Sum`, `Count`, `Subquery`/`OuterRef`, `Exists`, e.g. a member's balance or
    current plan end
- Model methods such as `Member.status()` and `balance_paise()` use preloaded data when the queryset brought it
  (`Member.objects.with_totals()`, `Subscription.objects.with_paid()`) and query for themselves otherwise. Lists,
  filters and summaries always load through those queryset methods, so one set of rules serves both and they can't
  disagree. Money checks inside a transaction reload fresh under the lock (see `take_payment`).
- **Filter, count and sum in the database**, not in Python loops over querysets. `qs.filter(...)`,
  `values().annotate()` and `aggregate()` are the defaults. If something can't be expressed in SQL, say why in a
  comment, and check it still holds for a gym with 5,000 members.
- **Indexes**: every field a list filters or sorts on is indexed, with `gym` first in composite indexes
  (`(gym, local_date)`, `(gym, taken_at)`). Add the index in the same change that adds the filter.
- Use `.only()`/`.values()` for exports and large reads. Use `.iterator()` for anything that walks a whole gym.
  Use `.exists()` instead of `.count() > 0`, and `.first()` instead of `[0]`.

### Pagination, filtering, search
- **Every list is paginated on the server** (`apps/core/params.Pages`: default 50, at most 100). The only
  exceptions are small fixed lists such as a member's notes. They set `pagination_class = None` and say why.
- **Counts come from the server**, never from counting the rows a screen happens to have loaded: a `count` on the
  page, a summary endpoint (`/api/checkins/summary/`, `/api/reports/summary/`) or a `counts` action
  (`/api/tasks/counts/`).
- **Filters are declared, not hand-parsed.** Use `filterset_fields` or a `FilterSet` for exact matches, `int_param`
  (`apps/core/params.py`) for ids read by hand, and `clock.parse_date` for dates. A bad value answers **400 with a
  field error, never 500** (`?branch=abc`). Document every parameter with `@extend_schema` so the web client is typed.
- **Search** is one `q` parameter with `icontains` over a few indexed columns (name, code, phone). Trim it, ignore
  anything shorter than 2 characters, and document it with `@extend_schema` `OpenApiParameter`.
- The web asks for a page and shows the design's **Load More** (`useXxxListInfinite` + `paged`/`pages` from
  `src/lib/hooks.ts` + `<LoadMore>`). It never asks for a big `limit` to avoid paging. Pickers (trainers, staff)
  ask for one page of 100, since a gym has far fewer. Search goes through `useSearch` (300 ms, 2+ characters).
  Filters live in the URL so Back keeps them.

### Writes and bulk work
- One business action is **one service call in one transaction**. Use `select_for_update()` wherever money or
  counts could race (as `take_payment` does).
- Bulk work uses `bulk_create` / `bulk_update` / `queryset.update()` in batches (`batch_size=500`). It never calls
  `.save()` in a loop. Imports and exports over about 1,000 rows run as background jobs (Celery, once added), not in
  the request.

## 4. Security

### Authentication
- JWT via simplejwt: access 30 min, refresh 30 days, rotated. **Rotated and signed-out refresh tokens are
  blacklisted** (`rest_framework_simplejwt.token_blacklist`, `BLACKLIST_AFTER_ROTATION`).
- **Login, refresh, QR check-in and device punch are rate limited** (`DEFAULT_THROTTLE_RATES`). Sign-in is limited
  per account (10/min) and, more loosely, per address (60/min), because a whole gym can share one Wi-Fi address.
  Throttle counts live in the cache: production with several workers sets `CACHE_URL` to Redis.
- Passwords: Django hashers and validators only. Never log, return or audit a password or token.
- The web keeps tokens in `localStorage`, so XSS means account takeover. Never render user text as HTML
  (`dangerouslySetInnerHTML` only for SVG we generate ourselves). Add no third-party scripts.

### Permissions and isolation
- **Every gym view uses `GymViewMixin` and states `roles` for every action.** `AllowAny` is only for login, refresh
  and device punch, each with its own check. The default is admin-only, so forgetting `roles` fails closed.
- **Every queryset starts from the gym**: `Model.objects.filter(gym=self.gym)`, or `member__gym=` for child tables.
  Then comes `in_my_branches` where branches matter, then the role narrowing (trainer: own members; member: self).
- **Every id that comes in is checked against the gym**: `GymPK` in serializers. Query-parameter ids only narrow an
  already-scoped queryset. Looking up any other object by a bare id (`Model.objects.get(pk=...)`) is a review blocker.
- A gym or record you can't see answers **404, never 403**. Don't confirm that it exists.
- **What a role may not see is left out of the serializer**, not hidden by the web (`TrainerMemberSerializer` has no
  amounts). Use a separate serializer per audience instead of `if role:` inside one.
- Support access is read-only and time-boxed by `InGym`. Don't add a write path for support.

### Input and output
- **All input goes through a serializer** (body) or a declared filter (query). Never read `request.data["x"]`
  directly. Give strings `max_length`, numbers bounds, choices `ChoiceField`.
- Money is integer paise everywhere. Validate `min_value=1` and an upper bound that makes sense.
- Errors use the standard shape. **Never return tracebacks, SQL or other gyms' data in a message.**
- Audit every change to money, access or history with `record(...)`, including who, before and after.

### Configuration
- Secrets come only from the environment. `.env` is never committed. Every server sets `PRODUCTION=true`, which
  refuses to start without `SECRET_KEY` or with `DEBUG=True` and turns on HTTPS-only settings (redirect, secure
  cookies, HSTS, the load balancer's forwarded protocol). Run `python manage.py check --deploy` before a release.
- Dependencies are pinned (`requirements.txt`, `package-lock.json`). Run `pip-audit` and `npm audit` before a release.

## 5. Code quality

- **Python**: format and lint with `ruff` (line length 120; not set up in the repo yet), type
  hints on service functions and anything in `core`.
  Names say what things are in the gym's words (`take_payment`, not `process_txn`).
- **TypeScript**: `strict`, no `any`, no `as never` / `as unknown as`. A cast means the OpenAPI schema is wrong, so
  fix the `@extend_schema` and regenerate.
- Functions do one thing and stay short (about 40 lines). Return early instead of nesting.
- Comments say **why**, not what. Docstrings are one or two plain sentences.
- **Code must run on Windows, macOS and Linux.** Nothing platform-specific (`strftime("%-I")` is Linux-only, so use
  a `clock` helper). Use `pathlib` for paths.
- Delete dead code. No commented-out blocks and no `TODO` without a name and a reason.
- After any endpoint or serializer change, regenerate the web client (see the root `CLAUDE.md`) in the same change.

## 6. Frontend

- **Server state lives in TanStack Query only.** Don't copy query data into `useState`. Derive it with `useMemo`.
  Writes go through `useAction` with the narrowest `refresh` prefixes (not the `"/api/"` default for a screen that
  touches one list).
- **One screen, few requests.** If a screen needs five calls to draw, add one summary endpoint instead (like
  `/api/reports/summary/`). Pass `enabled` to skip queries a role can't use.
- Every list has loading (`SkeletonRows`), empty (`Empty`) and error states. Every button that writes shows `busy`
  and can't be pressed twice.
- **Mobile first**: build at 390 px, check 360 and 430, then desktop (two columns inside 960 px). Tap targets are at
  least 44 px. Inputs use 16 px text with the right `inputMode`.
- Lazy-load heavy, rarely used parts with `next/dynamic` (QR scanner, QR generator, charts). Use `next/image` for
  photos. Keep the first load of the Home screen small.
- Role rules mirror the API (see `web/CLAUDE.md`), but **the API is the security**, so never rely on hiding.

## 7. Testing

**API (pytest).** Every endpoint gets, in `tests/test_<area>.py` using the `w` / `other` fixtures:
1. the main success path, asserting the response shape a screen depends on
2. **a role that must be refused** (403), and **another gym's ids** (404)
3. **branch scoping**: a receptionist at branch A can't see or write branch B
4. each `RuleBroken` it can raise, asserting the `code`
5. **a query budget**: create several rows, then `with django_assert_max_num_queries(N)` around the request, so an
   N+1 fails the build
6. audit rows for changes that must be audited

Services get direct unit tests for their rules: edge dates, month ends, freezes, part payments, races where they
matter. Use `transaction=True` tests with two connections for `select_for_update`. Fix the clock in tests (pass
`today`/`at`) rather than depending on when the tests run.

**Web.** Use Vitest for `src/lib` (formatting rupees with Indian grouping, `toPaise`, dates, `fieldError`) and for
non-trivial hooks. Use Playwright (`e2e/flows.spec.ts`) for each role's main flows on the demo gym at 390 px:
sign-in, add member + sell + collect, desk check-in, QR check-in, trainer view (no amounts visible).

**Before a change is done**, everything in "Checks before you say something is done" in the root `CLAUDE.md` passes
on your machine, and new code has the tests above. Fix a failing test. Don't skip it.

## 8. Reviews

A reviewer checks, in this order:
1. **Isolation and roles**: scoped queryset, `roles` on every action, `GymPK` on every id, other-gym and
   wrong-role tests.
2. **Money and history**: paise, transactions, locks, audit, nothing deleted.
3. **Queries**: query-budget test present, no per-row queries, indexes for new filters, pagination.
4. **Reuse**: nothing re-implemented that exists in the single sources above.
5. **Copy and design**: user-facing messages, design-system markup, 390 px.
