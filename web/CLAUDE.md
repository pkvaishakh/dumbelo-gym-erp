# Rackline web (Next.js 15 App Router, TypeScript)

Phone-first PWA for every role. Design at 390 px wide; everything must work from 360 to 430 px.
A tablet or desktop gets the same layout widened (two columns inside 960 px), never a sidebar.

## Layout

```
src/app/login                 shared sign-in
src/app/(app)/layout.tsx      SessionProvider (who, which gym, which branch) + bottom TabBar
src/app/(app)/<route>         one folder per screen; task screens are /…/new or /…/edit (no tab bar there).
                              A suspended gym shows features/paused everywhere but More (admins only)
src/app/(console)/console     the Console for Rackline admins: ConsoleProvider + ConsoleTabBar (Gyms, Requests, Prices,
                              More); gyms list, a gym, its Rackline plan (gyms/[id]/plan), New Gym, branch requests,
                              price lists and Add Price List, a gym's invoices (gyms/[id]/invoices: pending charges, Add
                              Charge), an invoice (invoices/[id]: Record Payment, Void Payment, Void Invoice) and its
                              print pages, WhatsApp (More → WhatsApp: the numbers, whatsapp/new for the shared one or
                              `?gym=` for a gym's own, whatsapp/[id]: Test Connection, webhook, credentials, templates),
                              Automation (More → Automation: Rackline's times; a gym's own are in Messages on its screen),
                              Server (More → Server: health, the jobs and Run Now, messages and webhook; checks again
                              every 30 s, every 3 s while a run waits or runs).
                              Its parts are in src/features/console/ (requests: RequestRow, RequestSheet; plan-sheets:
                              EditPlanSheet, MovePricesSheet; invoice-sheets: RecordPaymentSheet, VoidSheet,
                              AddChargeSheet, ChargeSheet; whatsapp: WhereFields, SecretField, EditAccountSheet,
                              CredentialsSheet, TemplateSheet; messages: HourField, DaysField, AutomationSheet, GymMessages;
                              server: RunBadge, jobLine, JobSheet with Run Now's confirm)
src/app/(app)/rackline-plan   the gym admin's Rackline plan, Add Branch to My Plan and its invoices (invoices/[id], print,
                              receipts/[pid]); open with More while the gym is paused, invoices and receipts too
src/components/ui.tsx         design-system pieces: Icon, Photo, Status, TaskStatus, Section, Stat, Field,
                              Chips, Seg, Choices, Sheet, Confirm, Empty, SkeletonRows, SearchField, MenuRow, Details
src/components/shell.tsx      HomeBar + Greeting, PageBar (tab screens), DetailBar (records), TaskBar (task screens),
                              TabBar per role, CreateSheet, BranchSheet
src/features/                 bigger parts shared by routes: homes, checkin (desk), self-checkin (QR), sell
                              (MemberPicker, PlanPicker, ActionBar, METHODS), staff-form, branch-form, members-ui,
                              money-out (PaySheet, DueSheet, bill and payslip badges), payroll (Breakdown, rateText),
                              recurring-form, money (MoveRow, MoveSheet, BranchMoneySheet), account-form, drawer (CountRow,
                              CountSheet), refunds (RefundSheet, RefundRows), rackline-plan (PlanCard, BranchRoom,
                              PlanPrices, AskStatus, proRataText: a gym's Rackline plan, for the gym and the Console),
                              rackline-invoices (InvoiceRowLink, InvoiceCard, InvoiceLines, PaymentRows, PrintFrame,
                              InvoicePaper, ReceiptPaper: the same invoice and receipt for the gym and the Console)
                              reports/ (range: useReportRange + ReportControls, period and branch in the URL; screen:
                              ReportScreen, ReportPrint, Download; parts: Lead, Trend, SeriesChart, BarList; one file per
                              category; categories: the registry)
src/lib/api.ts                fetch wrapper: token, refresh, X-Gym, ApiError; apiFetch is orval's mutator
src/lib/session.tsx           useSession(): me, role, gym, paused, branch, setBranch, signOut (gym app); useWho(): me,
                              signOut (both apps: avatar, account sheets); ConsoleProvider
src/lib/hooks.ts              useGet (loosely typed GETs), useAction (writes + refresh), fieldError
src/lib/format.ts             rupees, dates, clock times, greeting, STATUS_LABEL, gymToday (the gym's day, not the device's)
src/lib/types.ts              shapes of endpoints the schema leaves loose (summary, collection…)
src/lib/messages.ts           when each WhatsApp message goes out, in words (hourLabel, daysLabel, whenLabel, MESSAGE_TO)
src/lib/reports.ts            report categories, periods, MAX_MONTHS (the API's) and the range check
src/lib/report-rows.ts        each report as plain rows: its CSV (reportCsv) and its print page
src/lib/csv.ts                toCsv, plainRupees, download, statementCsv
src/api/gen/                  GENERATED by orval from openapi.yml. Never edit; run `npm run api`.
src/styles/                   tokens.css + rackline.css: the design system CSS. Don't restyle components here.
```

## Building screens

- **Use the design system's markup and classes** (`rl-*`). Before building or changing a screen, open the matching
  component doc in `../docs/design/components/` (e.g. `MembersList.md`, `MemberProfile.md`, `Attendance.md`) and
  follow its markup and rules. Reuse `ui.tsx`/`shell.tsx` pieces; add a new piece there only if the design has it.
- Screen kinds: **tab screen** (`PageBar`, list in a card, bottom nav), **record** (`DetailBar`, identity, actions,
  cards), **task screen** (`rl-app rl-app--task`, `TaskBar`, one-column form, `ActionBar`, ends in a `Sheet` with
  `Confirm`), **sheet** for small actions on a record.
- Colours only through tokens (`var(--ink)`, `var(--volt)`…). `volt` is a fill, never text on white. One `volt`
  (accent) action per screen at most. No new colours, fonts, shadows or radii.
- Icons: lucide-react through `<Icon as={X} size="sm" />` (1.75 stroke). Numbers big via `rl-stat__value`/`rl-figure`.
- Inputs: visible label above (`Field`), 16 px text, correct `inputMode`/`autoComplete`, "(optional)" on skippable
  fields, errors under the field saying what to do. Money typed in rupees, sent as paise (`toPaise`).
- Every list has a loading state (`SkeletonRows`) and an empty state (`Empty`) that says why and offers the way out.
- Role rules in the UI mirror the API: trainers never see amounts; receptionists see no revenue totals on Home;
  members see only themselves. Hide sections a role can't act on.
- Copy: second person, short, Title Case actions ("Collect ₹1,500"), sentence case everywhere else, `&apos;` in JSX.

## Data

- Reads: generated hooks, e.g. `useMembersList({ status: "due", branch })`; data is at `q.data?.data`.
  Loosely typed endpoints: `useGet<Summary>("/api/reports/summary/", { branch })`.
- Writes: `const a = useAction(); await a.run("/api/payments/", body, { refresh: ["/api/members/"] })`;
  show `a.error?.message` with `ErrorText`, disable the button with `a.busy`.
- Admin's branch filter comes from `useSession().branch` (null = all). Pass it to lists that take `branch`.
- Long lists page with Load More: `const q = useMembersListInfinite(params, { query: paged }); const { rows, count }
  = pages(q);` then `<LoadMore q={q} />`. Add an operation id to `orval.config.ts` to get an infinite hook. Never
  ask for a big `limit`; take counts from the API. Search text goes through `useSearch(q)`.
  Full rules: `../docs/standards.md`.

## Checks

`npm run typecheck`, `npm run lint`, `npm run test` (Vitest, `src/lib`), `npm run build`, and `npm run e2e` (API
running with the demo gym; first time: `npx playwright install chromium`).
Look at changed screens at 390 px before calling them done.
