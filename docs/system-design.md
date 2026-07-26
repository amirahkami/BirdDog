# BirdDog system design memory

Last updated: 2026-07-26

This is the current high-level design agreed during planning. It is not an implementation report. If an older statement in `PROJECT.md` conflicts with this document, this document records the newer decision until the documentation is reconciled.

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

Desired seniority is not settled yet and should not be added until tested and discussed.

## CV handling

- Accept PDF files up to 25 MB.
- Store the original PDF using the volume-based storage approach.
- Store file metadata, extracted text and structured facts in PostgreSQL.
- Python performs text extraction and OCR.
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

ESCO is a candidate role taxonomy for connecting related occupations. It is not approved until playground testing demonstrates useful results.

## Job pipeline

The intended high-level funnel is:

```text
discover -> collect -> normalize -> deduplicate -> validate
         -> classify/enrich -> assign to pools -> personalize/match -> serve
```

Important rules:

- Cheap deterministic checks run before AI.
- AI is used where language understanding is necessary.
- The system needs health checks and safe fallbacks between layers.
- A new pool may take time to build; the first user waits until useful results are ready.
- Existing pools serve current matches while refresh work runs in the background.

## Source strategy: provisional until retested

Earlier Docker playground tests selected an ATS-first strategy:

- Primary candidates: Personio, Greenhouse, Lever, Ashby, SmartRecruiters, Workable and Recruitee.
- Secondary remote feeds: WeWorkRemotely, Jobicy and Remotive.
- Discovery helpers: Common Crawl and, where appropriate, Bundesagentur company names.
- Previously rejected: Indeed, LinkedIn, StepStone, Xing and production use of Adzuna.
- Jooble remains untested.

Previous summaries reported clean full descriptions from ATS feeds and high noise from broad/remote feeds. The raw earlier job-source playground artifacts are no longer present, so the entire source strategy must be tested again before final approval.

When the same job appears in multiple sources, prefer the direct employer/ATS application URL. Exact source precedence and fallback behavior remain subject to the new tests.

## v1 matching direction

Matching combines:

1. Hard eligibility filters: active job, geography, work mode, employment type and explicit restrictions.
2. The user's primary desired job as the search anchor.
3. CV evidence: skills, experience, education, languages and relevant facts.
4. Closely related roles only when evidence supports the relationship.
5. A factual score and a clear explanation for the user.

The exact scoring formula, role classification, related-role logic and AI quality thresholds require playground benchmarks before implementation.

## Modular AI inference

- AI access uses provider adapters behind one internal interface.
- The administrator chooses the active provider in the admin dashboard.
- Current provider candidates include the existing OpenWebUI/Ollama service and KIConnect.
- More providers, such as the OpenAI API, can be added later without changing the pipeline.
- Provider health, model capability and fallback behavior must be visible to the administrator.
- Secrets must remain in environment/configuration storage and never in this document or the database as plain text.

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
- AI: modular provider adapters; OpenWebUI/Ollama and KIConnect initially, with providers such as OpenAI possible later.
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

## Required playground tests before implementation decisions

1. Retest job-source coverage, completeness, freshness, legal/technical usability and application links.
2. Test the canonical job, source-record and role-pool storage design.
3. Test exact and semantic deduplication; do not mix vectors from different embedding models.
4. Test ESCO for role normalization and related-role discovery.
5. Test location, remote/hybrid/on-site and employer-restriction detection.
6. Benchmark CV and job extraction/classification in German and English.
7. Benchmark both AI providers, different models, failures and processing time.
8. Simulate demand-driven pools, scheduling, expiry strikes and administrator controls.
9. Validate the complete funnel using varied jobseeker personas and roles.
10. Validate onboarding, first-search waiting, matches and admin frontend flows for usability, responsiveness and accessibility.

## Architecture approval gate

- The overall architecture is not approved merely because it is documented.
- Every uncertain architectural decision must be tested through Docker in `playground/`.
- Test results must include evidence, limitations and a clear recommendation.
- The user reviews and approves decisions one by one.
- Approved conclusions are copied into this tracked document.
- Production-feature development begins only after the overall architecture is approved.
