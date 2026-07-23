# BirdDog

**AI job-hunt bird dog that sifts every source and retrieves only the right-fit roles.**

Pick your field (a "niche"), and BirdDog gathers jobs daily, filters out the noise, and uses a
self-hosted LLM to read each promising job in full and score how well it fits you. No endless scrolling.

## Status

Milestones 1–3 are implemented: the Dockerized application foundation, seven-table data layer,
and invite-only authentication. Keycloak 26.7 protects the frontend and API. The initial `birddog`
administrator is the only user; all future users join by admin invitation. Development email is
captured by Mailpit.

## Quick start

```sh
cp .env.example .env    # replace every change-me value
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

## More

See [PROJECT.md](PROJECT.md) for the full architecture, data model, pipeline, and validation notes.
