# backend — FastAPI API and worker

Runs in the `api` container and shares its package with the `worker` container.

## Current foundation

- FastAPI with public API documentation disabled.
- Keycloak token validation and database user synchronization.
- Protected `/me` and administrator `/admin/status` endpoints.
- PostgreSQL with the approved 21-table v1 domain foundation and reversible Alembic migrations.
- Durable, idempotent work items with concurrent `SKIP LOCKED` claiming.
- Protected three-step onboarding endpoints under `/onboarding`.
- Private UUID-based PDF storage with extension, MIME, signature, size, page and encryption checks.
- APScheduler worker with PyMuPDF extraction and bounded German/English Tesseract OCR fallback.

Extracted text is stored and candidate-fact work is queued. Candidate-fact structuring, job ingestion,
matching and AI-provider adapters are not implemented yet.

## Layout

```text
app/
  core/        Settings, config, env loading
  cv/          Private storage, extraction and CV work processing
  db/          SQLAlchemy models and session
  ingestion/   Future job-source adapters
  matching/    Future filtering and matching pipeline
  llm/         Future modular AI-provider adapters
  repositories/ PostgreSQL persistence operations
  routers/     FastAPI route handlers
  schemas/     Pydantic request/response models
  worker/      APScheduler process and CV extraction task
migrations/    Alembic database migrations
tests/         Test suite (run inside the container)
```
