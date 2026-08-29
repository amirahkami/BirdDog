# BirdDog project plan

**AI-assisted job discovery and matching for jobseekers.**

## Current status

The reusable application foundation is implemented and runs with Docker Compose:

- Next.js frontend with Keycloak login and protected routes.
- FastAPI with token validation, user synchronization and protected admin status endpoint.
- PostgreSQL with pgvector and an initial reversible Alembic migration.
- Python worker with an APScheduler placeholder task.
- Keycloak 26.7 invite-only authentication.
- Mailpit for development invitation email.
- Protected three-step onboarding API.
- Private PDF storage with a 25 MB limit.
- German/English CV text extraction with bounded OCR fallback.

The frontend is a temporary foundation. The approved 21-table domain model, reversible migrations,
durable PostgreSQL work queue and CV extraction worker are implemented. Evidence-backed candidate
fact structuring is queued for the modular AI milestone. BirdDog's AI engine is confirmed as
KIConnect, an OpenAI-compatible inference API (verified 2026-08-29); it is not yet wired into the
application (Milestone 6). Job ingestion, pool behavior, matching and user job actions are not
implemented.

## Product boundary

- BirdDog is for jobseekers, not employers.
- Public registration is disabled; users join by administrator invitation.
- BirdDog finds and explains matches. Applications open on the original job website.
- Matching must use the user's stated goal and CV facts without unsupported guessing.

## Intended user flow

```text
accept invitation -> sign in -> complete short onboarding -> upload CV
-> request first role search -> admin approves new pool when needed
-> pool builds -> personalized matches become available
-> like, dislike or open the original application page
```

Onboarding collects one primary desired role, location/radius, accepted work modes, accepted
full-time/part-time options and a PDF CV up to 25 MB.

## Approved architecture

BirdDog uses demand-driven shared role pools. Comparable users share collected jobs, while matching
remains personal.

```text
onboarding -> CV extraction/OCR -> evidenced candidate facts

board discovery -> shallow source polling -> pool candidate routing
-> detail fetch -> normalize -> conservative deduplication
-> extract/enrich facts -> hard filters -> deterministic scoring -> matches
```

- On-site and hybrid jobs respect the user's radius.
- Fully remote jobs cover the EU, EEA and Switzerland.
- Cheap deterministic checks run before AI.
- AI providers are modular and administrator-selectable.
- Administrators control pools, refresh schedules, expiry rules and operational status.
- Stored jobs are never automatically deleted.

The detailed decisions are maintained in [docs/system-design.md](docs/system-design.md).

## Architecture status

The complete high-level architecture passed Dockerized playground benchmarks and was approved on
2026-07-26. Domain foundation and onboarding/CV extraction backend work are implemented.
Implementation follows the ordered milestones in [docs/implementation-plan.md](docs/implementation-plan.md),
with explicit approval before changes.

## Approved source direction

- Primary: Personio, Greenhouse, Lever, Ashby, SmartRecruiters, Recruitee and Workable.
- Secondary: Arbeitnow, Jobicy and We Work Remotely, subject to attribution and source terms.
- Remotive stays disabled until permission is clear.
- LinkedIn, Indeed, StepStone and Xing are not scraped.
- Current and historical Common Crawl indexes seed a persistent ATS board registry.

## Selected technology stack

- Frontend: Next.js, TypeScript, Tailwind CSS, shadcn/ui and TanStack Query.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2 and Alembic.
- Data: PostgreSQL with pgvector; volume-based PDF storage.
- Background work: Python worker with APScheduler.
- Authentication: Keycloak 26.7 with OIDC.
- Email: Mailpit in development; Mailjet in staging and production.
- AI: KIConnect (Inferenz NRW), an OpenAI-compatible inference API, as the main engine behind modular
  provider adapters; default model `mistral-small-4-119b`. More providers (e.g. OpenAI) may follow.
- Testing: pytest and Playwright, always through Docker Compose.
- Deployment: Docker Compose for development/staging; k3s with Helm for production.

Additional proven open-source components may be added when tests demonstrate a clear need.

## Repository structure

```text
BirdDog/
├── apps/
│   ├── backend/        FastAPI API, worker, models and migrations
│   └── frontend/       Next.js application
├── deployment/
│   ├── staging/        future VPS deployment
│   └── production/     future k3s/Helm deployment
├── docs/               durable design decisions
├── infra/              Keycloak, PostgreSQL and future infrastructure
├── playground/         ignored Dockerized experiments
├── tests/              end-to-end, smoke and load tests
└── docker-compose.yml  local development topology
```

## Branch strategy

- `dev`: local development and current working branch.
- `stage`: created later for VPS staging.
- `main`: created later for production.
- Promotion direction: `dev` -> `stage` -> `main`.

## Development environment

Create `.env` from `.env.example`, replace its placeholder secrets, then use Docker Compose:

```text
docker compose up --build
```

- Frontend: <http://localhost:22300>
- Keycloak: <http://auth.localhost:22080>
- Mailpit: <http://localhost:22025>
- Protected API: <http://localhost:22800>
