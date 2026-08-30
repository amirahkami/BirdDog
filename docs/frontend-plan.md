# BirdDog frontend plan

Created: 2026-08-29. This plan applies the approved design direction to the **current** frontend and
then builds the frontend for backend features that already exist. It is executed one small step at a
time; each step needs its own explicit green light and is verified in Docker before the next begins.

Nothing in this plan is built yet.

## Design basis

- Goal: replace job-hunt anxiety with confidence and clarity.
- Strictly mobile-first; primary buttons in the thumb zone, tap targets at least 44×44px.
- Job cards easy to scan at a glance.
- Base palette: deep navy/slate + off-white backgrounds.
- Indigo/violet for AI/smart features; emerald green for high match scores.
- AI is not a black box: show why a job fits (matching skills vs gaps), with "Why this match?" and
  "Not relevant" controls.
- Light, dark and system themes.

## Working rules

- Build one small step at a time; do not do everything at once.
- Backend and frontend are implemented alongside each other: every backend feature gets its frontend
  component in the same unit of work. This keeps features usable and makes bugs easier to catch and
  fix during development.
- Everything runs in Docker (`docker compose`).
- Every screen: mobile-first, light/dark, WCAG AA.
- Use the chosen stack (Next.js, TypeScript, Tailwind, shadcn/ui, TanStack Query).

## Phase A — Design skeleton on the current frontend

No new features; look and reusable parts only.

- A1 — Design tokens + theming: navy/slate + off-white, indigo (AI), emerald (match), semantic
  colors, type scale, spacing, radius; light/dark/system switch with no flash.
- A2 — Core components (skeleton set): button (thumb-zone ≥44px), input, card, chip/badge, app shell + nav.
- A3 — Restyle landing.
- A4 — Restyle admin (status page).

Login is out of scope: auth is Keycloak throughout, and its hosted login form is acceptable as-is for
now, so it is not restyled. Design effort focuses on the app's own screens.

## Phase B — Onboarding + CV frontend (backend already exists)

The backend endpoints exist (`GET /onboarding`, `PUT /onboarding/role`, `PUT /onboarding/preferences`,
`POST /onboarding/cv`); order is enforced role → preferences → CV.

- B0 — API wiring: proxy routes for the onboarding endpoints (same pattern as `/me`).
- B1 — Onboarding gate: after login, read `GET /onboarding`; if incomplete, route into the wizard.
- B2 — Step 1: desired role.
- B3 — Step 2: preferences (location, travel radius, work modes, employment types).
- B4 — Step 3: CV upload + processing status (poll `GET /onboarding`).
- B5 — Wizard shell tying steps, progress and status states together.

## Decisions to settle inside Phase B (not before)

1. Location → coordinates: the backend needs latitude/longitude, so Step 2 needs a place-search that
   returns coordinates. Choose the geocoding approach.
2. The Milestone 6 block: after CV upload, onboarding status stays at "processing" (final "ready"
   needs candidate-fact structuring, which is Milestone 6). Decide what the screen shows there.

## Status

Phase A complete (2026-08-29), verified in Docker (typecheck, route compile, token utilities generated):
- A1 — design tokens + theming: Tailwind v4, navy/slate tokens (light+dark), next-themes, shadcn base + Button.
- A2 — core components: Card, Badge, ThemeToggle, SiteHeader.
- A3 — landing restyled: mobile-first, themed, light/dark toggle.
- A4 — admin status restyled: Card + Badge, themed.
- Login left as the Keycloak entry: themed via base tokens, structure unchanged (not restyled).
- Legacy landing/admin plain CSS removed; only minimal login helper CSS remains.

Phase B in progress:
- Prerequisite done (2026-08-30): jobseeker test user `seeker` created in Keycloak (role `jobseeker`).
- B0 — onboarding API proxy routes (`/api/onboarding`, `.../role`, `.../preferences`, `.../cv`):
  done 2026-08-30. Verified: typecheck clean, unauthenticated route returns 401.
- B1 — onboarding gate (jobseekers with incomplete onboarding routed to `/onboarding`): done 2026-08-30.
- B2 — Step 1 desired role (functional, saves via `PUT /role`): done 2026-08-30.
- B5 — wizard shell + stepper: done 2026-08-30.
- B3 — Step 2 preferences: DONE 2026-08-30. Backend: `onsite_countries`/`remote_countries` (+ migration
  20260830_04), home conditional on on-site/hybrid, `pgeocode` geocode endpoint. Frontend: preferences
  step (work modes, home country+postal geocode, radius, on-site list, remote SVG map). Country map
  graduated from the removed `/preview` route. Verified: onboarding integration test passes; typecheck.
- B4 — Step 3 CV upload + status: DONE 2026-08-31. PDF upload (<=25 MB) via POST /api/onboarding/cv,
  then a status view that polls GET /api/onboarding for extraction_status. "Processing" decision:
  after upload it shows extraction progress; full analysis (facts) completes later at M6, so the copy
  says "matches will be ready soon" and the user proceeds to the dashboard.
- B5 wizard shell: done earlier.

Phase B is functionally complete (onboarding: gate + role + preferences + CV).

- Settings page (`/settings`): DONE 2026-08-31. Jobseekers edit role and preferences (reuses
  PreferencesStep with a "Save preferences" button); each section saves with a confirmation toast.
  Two-column on wide screens (container queries); CV moved out to `/cv`.

## Beyond Phase B (done 2026-08-31)

- **CV-fact extraction** (candidate half of M6): KIConnect wired in; `cv.facts` worker turns CV text
  into structured facts; shown on the dedicated `/cv` page.
- **`/cv` page**: CV file + replace + in-app **PDF viewer** (react-pdf/pdf.js, self-hosted worker,
  mobile-first) + the extracted facts.
- **Design polish**: Manrope typeface (next/font), a consistent type scale (`t-display/h1/h2/h3/
  lead/eyebrow`), `shadow-card` elevation; responsive/big-screen layouts (max-w-5xl pages, two-column
  `/cv` and Settings). Baseline design still has room to grow.
- **Auth**: fixed hourly logouts — 8h rolling session + Keycloak refresh-token rotation.

Parked / next: auto-clean old CVs on replace; redefine **M3 (roles & shared pools)** to move toward
matches; matching/job collection postponed. See memory for details.

Browser test: sign in as `seeker`.

Geography scope decision: no hard app-level country lock — the app supports a broad (EU) country set
(job sources are international), and each user defines their own geography (radius + two country
lists). Commute routing (car/bike/transit via OSRM/MOTIS) is a separate, regional, post-M7 feature.

Note: `birddog-web` has direct access grants disabled, so onboarding is tested via the browser
(log in as `seeker`), not password-grant scripts.
