# Rackline web app

The phone-first app every role uses (admin, receptionist, trainer, member), installable as a PWA.
Next.js 15 (App Router) + TypeScript, styled with the Rackline design system's CSS (`src/styles/`),
data through TanStack Query and a typed client generated from the API's OpenAPI schema.

## Run it

The API must be running first (see `../README.md`), with the demo gym seeded.

```powershell
cd E:\freelance-projects\rackline\web
npm install
copy .env.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                       # http://localhost:3000
```

Open it at phone width (browser dev tools, 390 px) or on your phone on the same Wi-Fi
(`http://<your PC's IP>:3000`, and add that address to the API's `CORS_ALLOWED_ORIGINS`).
Sign in with the demo logins in the main README.

## How it's put together

```
src/
  app/                 routes (App Router). (app)/ is everything behind sign-in
    login/             shared sign-in for every role
    (app)/home         one home per role (src/features/homes.tsx)
    (app)/members      list, profile (/members/[id]), Add Member (/members/new)
    (app)/attendance   day strip, members and staff, desk check-in
    (app)/tasks        admin assigns and tracks; staff start, update, finish
    (app)/payments/new, subscriptions/new, expenses/new, staff/new, branches/new   task screens
    (app)/checkin      member/staff self check-in: camera scan, or /checkin/<code> from the wall QR
    (app)/branches/[id]/qr   the printable wall QR poster
  api/gen/             generated client and types (do not edit; `npm run api` regenerates)
  components/          ui.tsx (design-system pieces), shell.tsx (headers, bottom nav, sheets)
  features/            screens' larger parts shared between routes
  lib/                 api.ts (fetch + token refresh + X-Gym), session.tsx (who, which gym/branch), format.ts
  styles/              tokens.css and rackline.css from the design system
```

- **Roles**: the bottom navigation and each screen follow the signed-in role. The API enforces the same
  rules, so hiding something here is only for clarity, never for security.
- **Gym and branch**: the gym goes on every request as `X-Gym`. Admins pick a branch (or all) from the
  greeting; staff work in their branch.
- **API client**: after changing the backend, regenerate the client:
  `cd ../api && python manage.py spectacular --file ../web/openapi.yml && cd ../web && npm run api`.
  Reads use the generated hooks (`useMembersList`...). Writes use `useAction()` in `src/lib/hooks.ts`,
  which shows the API's own error message and refreshes the lists it changed.
- **PWA**: `src/app/manifest.ts` and the service worker `src/app/sw.ts` (Serwist; on in `npm run build`
  only). The app shell is cached; API calls always go to the network.

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
npm run e2e        # end-to-end flows for every role, against the demo gym
```
