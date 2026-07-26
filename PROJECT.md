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

The frontend is a temporary prototype. The initial seven-table database schema is also provisional.
Job ingestion, CV processing, shared role pools, matching and user job actions are not implemented.

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

## Intended architecture

BirdDog uses demand-driven shared role pools. Comparable users share collected jobs, while matching
remains personal.

```text
discover -> collect -> normalize -> deduplicate -> validate
         -> classify/enrich -> assign to pools -> personalize/match -> serve
```

- On-site and hybrid jobs respect the user's radius.
- Fully remote jobs cover the EU, EEA and Switzerland.
- Cheap deterministic checks run before AI.
- AI providers are modular and administrator-selectable.
- Administrators control pools, refresh schedules, expiry rules and operational status.
- Stored jobs are never automatically deleted.

The detailed decisions are maintained in [docs/system-design.md](docs/system-design.md).

## Architecture approval gate

The overall architecture is not final. Before production-feature development, Dockerized playground
tests must validate sources, canonical storage, deduplication, role taxonomy, geography, CV handling,
AI providers, matching, scheduling, admin controls, end-to-end flow and frontend usability.

Test evidence stays in the ignored `playground/` directory. Approved conclusions are copied into the
tracked design documentation.

## Source status

Older tests suggested an ATS-first approach using direct employer feeds, with remote feeds only as
secondary sources. Their raw artifacts are no longer present, so coverage, quality, freshness,
application links and source precedence will be tested again before approval.

## Selected technology stack

- Frontend: Next.js, TypeScript, Tailwind CSS, shadcn/ui and TanStack Query.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2 and Alembic.
- Data: PostgreSQL with pgvector; volume-based PDF storage.
- Background work: Python worker with APScheduler.
- Authentication: Keycloak 26.7 with OIDC.
- Email: Mailpit in development; Mailjet in staging and production.
- AI: provider adapters for OpenWebUI/Ollama and KIConnect initially; more providers may follow.
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
