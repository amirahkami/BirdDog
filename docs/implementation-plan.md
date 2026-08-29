# BirdDog v1 implementation plan

The architecture is approved. This plan defines implementation order only. Every milestone requires
an explicit green light before code changes. All tests run through Docker Compose.

## Milestone 1 — domain foundation

Status: completed on 2026-07-26.

- Replace the provisional schema with users/profiles, CVs, roles/pools, sources/observations,
  canonical jobs/locations, work items, matches/actions and provider capabilities.
- Add reversible Alembic migrations, constraints and indexes.
- Add repositories/services and PostgreSQL integration tests.

## Milestone 2 — onboarding and CV processing

Status: completed on 2026-07-26. Candidate-fact structuring is deliberately handed to Milestone 6,
where provider selection, validation, evidence and fallback behavior are implemented together.

- Implement the three-step onboarding flow.
- Add safe PDF upload and private volume storage.
- Add PyMuPDF text extraction and bounded OCR fallback.
- Store extracted text and queue evidence-backed candidate-fact processing.

## Milestone 3 — roles and shared pools

- Add normalized role candidates, aliases and ESCO references.
- Add administrator approval for new pools and related-role links.
- Add pool lifecycle controls: approve, pause, resume, rebuild and drop.

## Milestone 4 — source registry and collection

- Implement the approved direct ATS adapters.
- Add persistent current/historical board discovery.
- Add conditional shallow polling, source health and execution history.
- Add attributed secondary sources after source-specific terms checks.

## Milestone 5 — canonical jobs and freshness

- Normalize source observations without losing provenance.
- Store multiple locations and geographic confidence.
- Add conservative duplicate candidates and administrator review.
- Implement two-strike availability with per-source observations and reactivation.

## Milestone 6 — modular AI enrichment

The confirmed engine is KIConnect (OpenAI-compatible); see "Modular AI inference" in the system design.

- Implement the KIConnect (OpenAI-compatible) provider adapter behind one internal interface, so other
  providers (e.g. OpenAI) can be added later.
- Wire configuration to KIConnect: replace the placeholder `OPENWEBUI_*` env vars with `KI_CONNECT_*`
  in `.env.example`, `docker-compose.yml` and `config.py` (config currently reads no AI keys), and
  populate `app/llm/` (currently empty).
- Default to `mistral-small-4-119b` (German-hosted, unlimited, function calling) for high-volume work;
  reserve the rate-limited GPT-5.x models for low-volume, high-value calls.
- Add model capability records, administrator selection, health and fallback order.
- Validate schemas and evidence; keep failed facts unknown or queued.
- Add local GeoNames resolution and workplace/restriction enrichment.

## Milestone 7 — matching and user actions

- Implement hard eligibility filters.
- Implement deterministic, explained match scoring.
- Add Matches, Liked and Disliked states with undo behavior.
- Ensure one user's actions never alter another user's results.

## Milestone 8 — production frontend and administration

- Replace the temporary UI using the approved responsive light/dark direction.
- Connect onboarding, pool progress, matches and user actions.
- Add protected admin views for pools, sources, workers, AI and execution history.
- Run Playwright task flows and accessibility tests at mobile, tablet and desktop widths.

## Milestone 9 — release hardening

- Run end-to-end, failure, load, backup and restore tests.
- Review source terms, attribution and stored-content boundaries.
- Prepare the future VPS staging deployment from `stage`.
- Prepare k3s/Helm production deployment from `main` only after staging approval.

## Working rule

Complete and verify one milestone before starting the next. Do not add Kafka, Elasticsearch,
microservices or a larger monitoring stack unless measured evidence later requires them.
