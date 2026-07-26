# frontend — Next.js application

Runs in the `web` container. Talks to the `api` service.

## Current foundation

- Keycloak login through NextAuth.
- Protected home and administrator routes.
- Authenticated internal proxy to FastAPI.
- Administrator foundation-service status page.

The current interface is a temporary prototype. It will be redesigned only after the complete
architecture and frontend direction pass playground tests.

## Layout

```text
src/
  app/          Current login, home and administrator pages
  components/   Future reusable UI components
  lib/          Authentication and backend helpers
```
