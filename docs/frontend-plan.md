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
- B3 — Step 2 preferences: pending the location→coordinates (geocoding) decision.
- B4 — Step 3 CV upload + status: pending (and the "processing" state decision).
Browser test: sign in as `seeker`.

Note: `birddog-web` has direct access grants disabled, so onboarding is tested via the browser
(log in as `seeker`), not password-grant scripts.
