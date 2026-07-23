# BirdDog

**AI job-hunt bird dog that sifts every source and retrieves only the right-fit roles.**

Pick your field (a "niche"), and BirdDog gathers jobs daily, filters out the noise, and uses a
self-hosted LLM to read each promising job in full and score how well it fits you. No endless scrolling.

## Status

Concept and architecture are finalized and validated in the playground (coverage, accuracy, scale,
end-to-end). The containerized application foundation is running: Next.js, FastAPI, APScheduler,
and PostgreSQL with pgvector. Product features are the next development phase.

## Quick start

```sh
cp .env.example .env    # then set OPENWEBUI_API_KEY when AI integration begins
docker compose up --build
```

- Web: http://localhost:22300
- API: http://localhost:22800

The status page verifies the frontend, API, and database connection. The worker runs the daily
APScheduler schedule; ingestion tasks will be added in a later milestone.

## More

See [PROJECT.md](PROJECT.md) for the full architecture, data model, pipeline, and validation notes.
