# BirdDog

**AI job-hunt bird dog that sifts every source and retrieves only the right-fit roles.**

Pick your field (a "niche"), and BirdDog gathers jobs daily, filters out the noise, and uses a
self-hosted LLM to read each promising job in full and score how well it fits you. No endless scrolling.

## Status

Concept and architecture are finalized and validated in the playground (coverage, accuracy, scale,
end-to-end). **No application code yet** — the containers are placeholders while we wait for the green light.

## Quick start

```sh
cp .env.example .env    # then set OPENWEBUI_API_KEY
docker compose up
```

- Web: http://localhost:3000
- API: http://localhost:8000

> `api`, `web`, and `worker` are placeholder containers for now; `db` (Postgres + pgvector) is fully functional.
> Everything runs in Docker — nothing executes on the host.

## More

See [PROJECT.md](PROJECT.md) for the full architecture, data model, pipeline, and validation notes.
