# backend — FastAPI API and worker

Runs in the `api` container and shares its package with the `worker` container.

## Current foundation

- FastAPI with public API documentation disabled.
- Keycloak token validation and database user synchronization.
- Protected `/me` and administrator `/admin/status` endpoints.
- PostgreSQL connectivity, seven provisional SQLAlchemy models and a reversible Alembic migration.
- APScheduler worker with a placeholder pipeline task.

Job ingestion, CV processing, matching and AI-provider adapters are not implemented. Their design
must pass playground tests before the provisional schema is changed.

## Layout

```text
app/
  core/        Settings, config, env loading
  db/          SQLAlchemy models and session
  ingestion/   Future job-source adapters
  matching/    Future filtering and matching pipeline
  llm/         Future modular AI-provider adapters
  routers/     FastAPI route handlers
  schemas/     Pydantic request/response models
  worker/      APScheduler process and placeholder task
migrations/    Alembic database migrations
tests/         Test suite (run inside the container)
```
