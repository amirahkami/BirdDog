# BirdDog

**AI job-hunt bird dog that sifts every source and retrieves only the right-fit roles.**

BirdDog is an invite-only assistant for jobseekers. It will build shared job pools on demand and
produce personal matches using each user's desired role, preferences and CV facts.

## Status

The Dockerized foundation is implemented: frontend, API, worker, PostgreSQL, Keycloak, Mailpit,
approved v1 domain schema and protected administrator status page. The protected onboarding API,
private PDF storage and German/English CV text extraction with OCR fallback are also implemented.

The current frontend is a temporary foundation UI; onboarding is currently API-only. Candidate-fact
structuring, job ingestion, role pools and matching are not implemented. The v1 architecture and
frontend direction passed Dockerized playground tests and were approved.

## Quick start

Create `.env` from `.env.example` and replace every `change-me` value. Then start the complete local
environment with Docker Compose:

```text
docker compose up --build
```

- Web: http://localhost:22300
- Keycloak: http://auth.localhost:22080
- Mailpit: http://localhost:22025
- API: http://localhost:22800 (protected; public docs are disabled)

Sign in as `birddog`; its local password is `BIRDDOG_ADMIN_PASSWORD` in `.env`. Service status is
available only in the app's admin dashboard. To invite a user, open the BirdDog realm in Keycloak,
then use **Organizations → BirdDog → Members → Invite member**. Mailpit receives the development
email. Public registration is disabled.

## Documentation

- [System design](docs/system-design.md): approved v1 architecture and operating rules.
- [Project plan](PROJECT.md): current status, boundaries and next phase.
- [Implementation plan](docs/implementation-plan.md): approved development order.
