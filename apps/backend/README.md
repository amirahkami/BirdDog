# backend — FastAPI API and worker

Runs in the `api` container (and shares code with `worker`). Talks to
Postgres + pgvector and the external self-hosted LLM (OpenWebUI + Ollama).

**No application code yet — this is the planned structure only.**

## Layout

```text
app/
  core/        Settings, config, env loading
  db/          SQLAlchemy models + session; pgvector setup
  ingestion/   Job ingestion
    sources/   One adapter per source: arbeitnow, adzuna, remotive, ats
  matching/    The funnel: structured filter → embedding rank → LLM rerank
  llm/         OpenWebUI / Ollama client (native /ollama/api/chat, format=json)
  routers/     FastAPI route handlers (criteria, matches, health)
  schemas/     Pydantic request/response models
migrations/    Alembic database migrations
tests/         Test suite (run inside the container)
```
