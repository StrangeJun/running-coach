# Current status

## Phase

Garmin ingestion MVP: TASK-003 activity persistence/import API complete; real-account validation pending.

## Completed

- Repository/GitHub connection, Codex setup, lightweight AI docs, and privacy ignore rules.
- TASK-001: Next.js/TypeScript/Tailwind scaffold, FastAPI `/health`, and SQLite foundation.
- TASK-002: isolated Garmin client, session reuse, local login/MFA CLI, recent-run selection, and six-field normalization.
- TASK-003: SQLite activity storage keyed by `external_activity_id` and `POST /api/garmin/import-latest`. New imports return 201/`imported`; duplicates return 200/`already_exists` with the original stored record. Concurrent imports cannot create duplicate rows.
- Setup, API responses, and check commands documented in the root README.

## Current decisions

Personal use; user-triggered imports only; no background polling; SQLite for MVP; Garmin behind an adapter boundary; deterministic analysis before LLM coaching. `garminconnect==0.3.17`; Python 3.12+. API uses saved tokens only; initial login/MFA stays in the CLI. Configuration and field units live in the root README.

## Not implemented

Activity read API, frontend API consumption, analysis engine, OpenAI coaching, and training planner.

## Validation and limitations

- All 63 backend tests pass with synthetic data and mocked Garmin access, including repeated/concurrent imports, restart persistence, and API failure paths. `pip check`, CLI help, diff, and privacy checks pass.
- Real-account login, session reuse, and end-to-end import remain unverified; validate locally using the root README. Never commit tokens or personal activity data.
- Recent-run selection remains bounded and limited to recognized running types. Duplicate imports preserve the first record; metric updates are not synchronized.
- Existing limitations: upstream Starlette/AnyIO test warning and five development-only npm ESLint advisories; TASK-001 production npm audit was clean. Frontend unchanged in TASK-003.

## Next task

**TASK-004 — Read stored activity data**

Add a read-only latest-activity API with empty-state handling and synthetic-data tests. Keep retrieval independent of Garmin access; defer frontend integration, analysis, and coaching.
