# Current status

## Phase

Garmin ingestion MVP preparation; TASK-001 application scaffold complete.

## Completed

- Git repository initialized and GitHub repository connected; Codex configured.
- MVP workflow and manual “Import Latest Run” interaction decided.
- Lightweight AI documentation and privacy ignore rules established.
- TASK-001: Next.js/TypeScript/Tailwind landing page, FastAPI application, configurable local SQLite connection foundation, and `/health` endpoint.
- Backend tests and local setup/check commands documented in the root README.

## Current decisions

Personal use; manually triggered Garmin import; no background polling; SQLite for MVP; Garmin isolated behind an adapter/service boundary; deterministic analysis before LLM coaching.

## Not implemented

Garmin integration, normalized activity model and persistence schema, analysis engine, OpenAI coaching, training planner, and frontend API consumption.

## Validation and limitations

- Four backend tests, `pip check`, frontend lint/typecheck/production build, live server smoke checks, and diff/privacy checks pass.
- Production npm audit is clean. Full npm audit reports five high-severity advisories in the development-only ESLint dependency chain; the suggested fix downgrades the Next.js lint configuration and was not applied.
- Backend tests emit an upstream Starlette/AnyIO deprecation warning. No activity tables or import controls exist yet.

## Next task

**TASK-002 — Normalized activity model and persistence**

Define a minimal `NormalizedActivity` with explicit units and missing-data behavior; add SQLite activity storage and tests using synthetic fixtures. Keep domain data independent of Garmin payloads.
Do not implement Garmin integration or LLM coaching in this task.
