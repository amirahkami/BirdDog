# CareerFox

**AI-powered job search that saves you time in your specific field.**

Tell CareerFox what you're looking for — role, location, seniority, remote or on-site — and it scans job boards, filters out the noise with a self-hosted LLM, and delivers matches that actually fit. No more endless scrolling through irrelevant listings.

## Status

Pre-development. Concept refined and validated; infrastructure scaffolded with Docker Compose. **No application code yet.**

## v1 scope

- **Users:** skilled but unemployed professionals seeking the right role.
- **Vertical:** UX designers (single field first).
- **Region:** Munich or remote (German + English postings).
- **Input:** set criteria once — role, location, remote/on-site, keywords.
- **Delivery:** review curated matches on a web dashboard.
- **Match card:** fit score + a short "why it fits" rationale + apply link.
- **Feedback:** thumbs up/down that nudges future ranking.
- **Rationale language:** German + English.

## Architecture

| Component | Tech | Role |
|---|---|---|
| `web` | Next.js | Dashboard: enter criteria, review matches |
| `api` | FastAPI | REST API; orchestrates ingestion + matching |
| `worker` | Python | Scheduled job ingestion + the matching funnel |
| `db` | Postgres + pgvector | Jobs, users, criteria, matches, embeddings |
| LLM | Self-hosted OpenWebUI + Ollama (external) | Reads full job descriptions to judge fit |

Everything runs via **Docker Compose**; nothing is executed on the host. The LLM lives on an existing external server (`openwebui.futuristic.team`) and is reached over the network.

## Project structure

```text
CareerFox/
├── docker-compose.yml      # db + api/web/worker services
├── .env.example            # config template (copy to .env)
├── PROJECT.md
├── api/                    # FastAPI backend (+ worker)
│   ├── app/
│   │   ├── core/           # settings / config
│   │   ├── db/             # models, session, pgvector
│   │   ├── ingestion/
│   │   │   └── sources/    # arbeitnow, adzuna, remotive, ats adapters
│   │   ├── matching/       # funnel: filter → embed → LLM rerank
│   │   ├── llm/            # OpenWebUI / Ollama client
│   │   ├── routers/        # API endpoints
│   │   └── schemas/        # Pydantic models
│   ├── migrations/         # Alembic
│   └── tests/
└── web/                    # Next.js frontend
    └── src/
        ├── app/            # pages (criteria form, matches dashboard)
        ├── components/     # UI components
        └── lib/            # API client
```

Directories hold placeholder markers (`README.md` / `.gitkeep`) until development begins.

## Matching pipeline (planned)

A funnel that spends expensive LLM tokens only where they matter:

1. **Structured filter** (SQL) — role / location / remote / keywords → thousands to hundreds.
2. **Embedding rank** (multilingual, pgvector) — hundreds to dozens.
3. **LLM deep read** — self-hosted model reads full descriptions of the top ~20–40, returns a fit score + a short "why it fits" rationale (German or English).
4. **Store** — matches persisted for the dashboard.

Key: each job is embedded **once at ingest** (shared across users), so LLM cost scales with `users × top-N`, not `users × all jobs`.

## LLM

- **Serving:** self-hosted OpenWebUI backed by Ollama.
- **Matcher:** `qwen2.5:14b-instruct` (validated on German/English fit-scoring). Fast tier: `qwen2.5:7b-instruct`.
- **Embeddings:** `bge-m3` (multilingual, DE + EN).
- **Integration note:** call the native `/ollama/api/chat` endpoint with `"format":"json"` — the OpenAI passthrough is disabled on the server.

## Data sources (planned)

Anchor on **Arbeitnow** (DE + remote, free API), **Adzuna** (DE endpoint), **Remotive** (remote design), plus a curated **ATS** list (Greenhouse / Lever / Ashby). No LinkedIn/Indeed scraping in v1.

## Running

```sh
cp .env.example .env    # then set OPENWEBUI_API_KEY
docker compose up
```

- Web: http://localhost:3000
- API: http://localhost:8000

> `api`, `web`, and `worker` are placeholder containers until development begins; `db` (Postgres + pgvector) is fully functional.

## Open questions

- Rationale language policy — match the posting vs. user-selectable (both German + English supported).
- Match refresh cadence — hourly / daily.
- Final data-source shortlist (Arbeitnow / ATS boards / Remotive / Adzuna-DE).
- Whether to build a small labeled eval set for matching quality.
