# frontend — Next.js application

Runs in the `web` container. Talks to the `api` service.

The foundation includes a status page and an internal proxy to the FastAPI health endpoint.

## Layout

```text
src/
  app/          Next.js App Router pages (criteria form, matches dashboard)
  components/   Reusable UI components
  lib/          API client + shared helpers
```
