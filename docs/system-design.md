# BirdDog system design memory

Last updated: 2026-08-29

This is the approved v1 architecture. It records design decisions, not implementation status.

## Product boundary

- BirdDog serves jobseekers, not employers.
- BirdDog discovers and matches jobs. Applications remain the user's responsibility.
- The Apply action opens the original job website.
- Results must be based on job and CV facts, not unsupported guesses.
- The v1 system should be useful without overengineering.

## Users and access

- Public registration is disabled.
- Keycloak provides authentication.
- The initial administrator is the only built-in user.
- Every additional user joins through an administrator invitation.
- Initial roles are `admin` and `jobseeker`. More roles may be added later.
- All application pages and status information are protected by Keycloak.

## First-time onboarding

Keep onboarding short. Collect everything required to begin the first search:

1. One primary desired job, entered in the user's own words.
2. Home/base location and on-site/hybrid travel radius.
3. Accepted work modes: on-site, hybrid and/or fully remote.
4. Accepted employment types: full-time and/or part-time.
5. CV upload.

Do not force users to enter multiple desired jobs. The desired job is the anchor; the CV provides evidence and may support closely related roles.

Do not ask for desired seniority during onboarding. Job seniority and experience requirements are
extracted when explicitly stated and used as explained soft matching signals.

## CV handling

- Accept PDF files up to 25 MB.
- Accept no more than 50 pages.
- Validate the extension, MIME type, PDF signature and parser result.
- Reject encrypted or damaged PDFs.
- Store the original PDF using the volume-based storage approach.
- Use private UUID-based filenames and atomic writes.
- Store file metadata, extracted text and structured facts in PostgreSQL.
- Python performs text extraction and OCR.
- OCR must have a bounded execution time.
- AI converts extracted content into structured facts.
- German and English CVs are required for v1. French may be added later.

## Geographic rules

- Assume users can pursue relevant work across the supported European area. BirdDog does not manage permits, tax or employment paperwork.
- On-site and hybrid jobs must fall within the user's configured radius.
- Fully remote jobs may be anywhere in the EU, EEA or Switzerland.
- Worldwide remote jobs are outside the current scope.
- Explicit employer residency/location restrictions should be rejected as early as possible.
- If a restriction is unclear, allow the job to continue through later pipeline checks instead of discarding it prematurely.

## Demand-driven shared job pools

- Do not ingest every job in the world upfront.
- The first new search demand creates a proposed role pool.
- An administrator approves the new pool before it begins collecting jobs.
- Users with comparable role demand share the same pool.
- Each user receives different matches from that pool based on their CV, location and preferences.
- Pools have no fixed job-count cap. Efficiency comes from layered filtering and shared processing.
- Role pools remain logically separate but may be linked when roles are genuinely related.
- AI may suggest related roles or links; an administrator must approve them.
- Cross-skill jobs may link to multiple role pools without duplicating the canonical job.
- Administrators can approve, pause, resume, rebuild or drop pools.

ESCO is an approved versioned, multilingual reference vocabulary for role candidates and aliases. It
must not automatically decide a role mapping. Confidence rules and administrator approval control
pool creation and related-role links. Embeddings may retrieve candidates but may not make the final
decision.

## Job pipeline

The approved high-level funnel is:

```text
onboarding -> CV extraction/OCR -> evidenced candidate facts

board discovery -> shallow source polling -> cheap pool candidate routing
-> detail fetch -> normalize source observations -> conservative deduplication
-> deterministic fact extraction -> AI for unresolved facts
-> hard eligibility filters -> deterministic scoring -> personal matches
```

Important rules:

- Cheap deterministic checks run before AI.
- AI is used where language understanding is necessary.
- The system needs health checks and safe fallbacks between layers.
- A new pool may take time to build; the first user waits until useful results are ready.
- Existing pools serve current matches while refresh work runs in the background.

Source discovery and shallow polling are shared globally. Detail fetching and AI enrichment run only
for candidates relevant to active pools. Enriched canonical facts are cached and reused; AI is never
called for every user-job pair.

## Approved source strategy

- Primary direct ATS sources: Personio, Greenhouse, Lever global/EU, Ashby, SmartRecruiters,
  Recruitee and Workable.
- Secondary sources with required attribution and terms: Arbeitnow, Jobicy and We Work Remotely.
- Remotive remains disabled until written permission clarifies its terms.
- LinkedIn, Indeed, StepStone and Xing are not scraped.
- EURES and Bundesagentur may be added later through approved partnership/access paths.
- Common Crawl current and selected historical indexes discover ATS boards. Every board is validated
  against its official live endpoint before use.

Prefer direct employer/ATS facts and application URLs. Preserve attribution and source provenance.
Source-specific minimum polling intervals and terms override administrator scheduling preferences.

## Canonical job and data boundaries

Keep these concepts separate in PostgreSQL:

- users, profiles, preferences, CV documents and evidenced CV facts;
- role concepts, aliases, pools and administrator-approved pool relationships;
- source adapters, boards, executions and durable work items;
- source job observations with provenance and first/last-seen state;
- canonical jobs, multiple job locations and observation links;
- canonical job-to-pool links;
- personal matches, explanations, likes and dislikes;
- AI provider/model capabilities, health and routing state.

Never merge automatically on company and title alone. Stable IDs are authoritative only inside their
source namespace. Auto-merge only high-confidence identities; uncertain candidates remain separate or
enter administrator review. One canonical job may belong to several pools.

## v1 matching direction

Matching combines:

1. Hard eligibility filters: active job, geography, work mode, employment type and explicit restrictions.
2. The user's primary desired job as the search anchor.
3. CV evidence: skills, experience, education, languages and relevant facts.
4. Closely related roles only when evidence supports the relationship.
5. A factual score and a clear explanation for the user.

Hard filters decide availability, approved pool role, geography, work mode, employment type, explicit
residence restrictions and explicit legal/professional requirements. Missing facts lower confidence
instead of silently rejecting a job. Skills, seniority and experience gaps are soft, explained signals,
so suitable stretch jobs remain visible.

AI extracts evidence-backed facts. Deterministic application policy performs hard filtering and final
scoring. Every score shown to a user must include understandable reasons.

## Modular AI inference

- The confirmed AI engine is KIConnect (Inferenz NRW), an OpenAI-compatible inference API at
  `https://chat.kiconnect.nrw/api/v1` (verified working 2026-08-29). It is BirdDog's main AI engine for v1.
- AI access still uses provider adapters behind one internal interface, so additional providers (e.g.
  the OpenAI API) can be added later without changing the pipeline. The earlier self-hosted
  OpenWebUI/Ollama plan is dropped; it was never built.
- The administrator chooses the active model in the admin dashboard.
- Only API-enabled KIConnect models are usable by the backend. Two catalog models are Frontend-only
  and excluded: `mistral-small-3.2-24b` and the image model `gpt-image-2`.
- Usable text models (all support function calling and streaming):
  - `mistral-small-4-119b-2603` — Germany (Inferenz NRW), 262k context, unlimited rate,
    temperature-adjustable. Default workhorse for high-volume extraction and enrichment.
  - `gpt-oss-120b` — Germany (Inferenz NRW), 131k context, unlimited rate.
  - `gpt-5.5`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.3-codex`, `gpt-5.2` — Azure EU, 400k context,
    rate-limited (15–100 messages/hour). Reserved for low-volume, high-value calls.
- Model selection is driven by rate limits and data residency: only the German-hosted models are
  unlimited and keep personal CV data in Germany (preferred for GDPR); the Azure GPT-5.x models are
  capped and sit in the EU. The per-hour message limits are documented from the KIConnect chat
  frontend and are not yet confirmed to apply identically to API usage.
- Embedding models (endpoint `v1/embeddings`) are available if needed: `qwen3-embedding-8b` and
  `e5-mistral-7b-instruct` (Germany) and `text-embedding-3-small` (Azure EU). Embeddings remain
  optional; the earlier decision that they are not required for v1 still stands.
- Provider/model health, capability, latency, safe concurrency and fallback behavior must be visible
  to the administrator.
- Invalid AI output is rejected. Unsupported or failed facts remain unknown or enter review.
- The KIConnect API key (`KI_CONNECT_API_KEY`) remains in environment/configuration storage and never
  in this document or the database as plain text.
- The official KIConnect model catalog is archived as screenshots in `docs/kiconnect/`.

## User match actions

- Like: move the job to the Liked list and hide it from Matches.
- Unlike: remove it from Liked and return it to Matches when still active.
- Dislike: hide it only for that user and place it in a separate Disliked list.
- Users can undo individual dislikes or clear the Disliked list.
- One user's feedback never hides a job from another user.
- An expired liked job remains visible as `Unavailable` with a distinct style.
- Learning from likes/dislikes is deferred to version 3.

## Freshness and expiry controls

Administrators control freshness settings from the admin dashboard, with clear descriptions and safe limits:

- Global refresh default: 24 hours.
- Refresh range: 1 hour to 7 days.
- Per-pool refresh override is allowed.
- Default expiry threshold: 2 consecutive missing checks (two strikes).
- Expiry threshold range: 1 to 5 strikes.
- Per-pool strike override is allowed.
- A successful reappearance resets strikes to zero and reactivates the job.
- A source-wide failure gives jobs no strikes.
- A strike is added only after a successful source check where that specific job is missing.
- Jobs are never automatically deleted.
- Administrators can reset strikes or manually mark jobs active/unavailable.

## Simple operational monitoring

Keep initial monitoring inside BirdDog's protected admin dashboard:

- Source, pool, worker and AI-provider status.
- Last successful run and next scheduled run.
- Run duration and job counts.
- Latest useful error message.
- Execution history stored in PostgreSQL.

Prometheus, Grafana and a larger observability stack are postponed until they are justified.

## Frontend product requirements

- Modern, professional visual direction suitable for a trusted job-search product.
- Responsive, mobile-first layouts.
- Light, dark and system theme modes.
- Clear information hierarchy, navigation and page structure.
- Accessible semantic colors with at least WCAG AA contrast.
- Consistent typography, spacing, design tokens and reusable components.
- Strong loading, progress, empty, success, warning and error states.
- Keyboard navigation, visible focus and screen-reader support.
- Useful visuals for matching, pool-building progress and operational status when they improve understanding.
- Avoid decorative clutter and a generic template-dashboard appearance.

Frontend approval requires Dockerized responsive, accessibility and task-based usability checks in
the playground. The current frontend is only a replaceable foundation prototype; its authentication
and API integration may be retained.

## Settled technology stack

- Frontend: Next.js, TypeScript, Tailwind CSS, shadcn/ui and TanStack Query.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2 and Alembic.
- Database: PostgreSQL with pgvector.
- Background work: Python worker with APScheduler.
- Authentication: Keycloak 26.7 with OIDC.
- Email: Mailpit in development; Mailjet in staging and production.
- CV processing: PyMuPDF with an OCR fallback.
- AI: KIConnect (Inferenz NRW), an OpenAI-compatible inference API, as the main v1 engine behind a
  modular provider interface; default model `mistral-small-4-119b`, with providers such as OpenAI possible later.
- File storage: Docker volumes initially; Kubernetes persistent volumes in production.
- Development and staging: Docker Compose.
- Production: k3s with Helm.
- Package tooling: `uv` for Python and `pnpm` for the frontend.
- Testing: pytest and Playwright.
- Initial monitoring: BirdDog's admin dashboard with execution history in PostgreSQL.

Additional proven open-source components may be added when they provide clear value. Avoid adding infrastructure without a demonstrated need.

## Deployment and branches

- Local development: Docker Compose on branch `dev`.
- Staging later: VPS deployment from branch `stage`.
- Production later: k3s deployment from branch `main`.
- Only `dev` exists locally at the current development stage.

## Architecture validation status

The architecture passed Dockerized playground tests and was approved decision by decision on
2026-07-26. Evidence covered job sources, CV processing, ESCO, geography, workplace classification,
AI providers, embeddings, deduplication, matching, PostgreSQL workers, freshness, resilience, scale,
responsive frontend flows and accessibility.

Important measured boundaries:

- ESCO and embeddings retrieve candidates but are unsafe as final decision-makers.
- Structured ATS facts are more reliable than detecting workplace mode from incomplete text.
- PostgreSQL durable work items with `FOR UPDATE SKIP LOCKED` are sufficient for v1.
- No evidence currently justifies microservices, Kafka, Elasticsearch, a separate queue, Prometheus or
  Grafana for v1.
- Production use of each job source still requires terms/attribution review.

The concrete v1 AI engine was confirmed as KIConnect on 2026-08-29 (see "Modular AI inference"),
replacing the earlier unbuilt self-hosted OpenWebUI/Ollama plan.

Implementation follows [the implementation plan](implementation-plan.md). Each milestone still needs
an explicit green light before code changes.
