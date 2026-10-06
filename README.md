# Running Coach

Personal Garmin running analysis and coaching. The application has a static Next.js landing page, a FastAPI import endpoint, and local SQLite activity storage. A standalone Garmin access command handles initial login.

## Local setup

Requirements: Node.js 20.9+ and Python 3.12+ (verified with Node 24 and Python 3.14).

Backend, from the repository root:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`GET http://127.0.0.1:8000/health` checks SQLite connectivity; API docs are at `/docs`. Startup creates `data/running_coach.sqlite3` at the repository root. Set `RUNNING_COACH_DB_PATH` in the backend environment to override it; relative paths resolve from the working directory. Database files remain local and ignored. Startup creates the activities table without removing existing records.

Frontend, in another terminal from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. The landing page does not call the backend yet.

## Checks

```sh
cd backend
.venv/bin/pytest
.venv/bin/python -m pip check
```

```sh
cd frontend
npm run lint
npm run typecheck
npm run build
```

`npm run start` serves the production frontend after a build. Use synthetic data for tests; never commit local credentials or personal run data.

For project context and task-specific guidance, start with [docs/AI/README.md](docs/AI/README.md).

## Personal Garmin access (TASK-002)

Install the updated backend requirements, then run manually from `backend/`:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m app.garmin_cli
```

The command tries the saved session first. If login is required, enter your email, hidden password, and MFA code if requested. Tokens are reused and refreshed by the library, stored by default in the ignored repository-root `.garminconnect/` directory. `--token-dir PATH` selects a dedicated alternate token directory; keep it outside tracked files. Credentials are never written by the application. The library stores tokens with owner-only permissions.

The adapter uses [garminconnect 0.3.17](https://github.com/cyberjunky/python-garminconnect), an unofficial personal-use client. Old Garth session files are not supported; authenticate once to create the current token format.

The command requests the latest 50 running activities (`--limit 1–100`), recognizes common running variants, and selects the newest UTC start time. It prints only `external_activity_id`, `date` (UTC ISO timestamp), `distance_m`, `duration_s` (Garmin duration, not elapsed duration), `average_heart_rate_bpm`, and `average_cadence_spm`. Missing/zero sensor values become `null`; cadence is used as steps/minute without doubling. Invalid required fields fail explicitly.

Exit codes: `0` for a run, `1` for access/data failure or cancellation, `2` when no recognized run is found in the recent window (also used for invalid CLI arguments). Output is personal data: do not commit it. The standalone CLI saves tokens but no activity payloads, GPS, FIT files, or database records. Use the import API below to store normalized activities.

Backend tests mock the Garmin client and never need an account. Real-account access must be checked locally with this command; it has not been validated by automated tests.

## Import latest run (TASK-003)

Authenticate locally with the Garmin CLI first, then start the backend as above:

```sh
curl -X POST http://127.0.0.1:8000/api/garmin/import-latest
```

The endpoint uses saved tokens without credential/MFA prompts. It defaults to the CLI's repository-root `.garminconnect/` directory. If the CLI used `--token-dir PATH`, set `RUNNING_COACH_GARMIN_TOKEN_DIR=PATH` in the backend environment to use the same directory.

| Result | HTTP | Response |
| --- | --- | --- |
| New run stored | 201 | `{"status": "imported", "activity": {...}}` |
| Existing run | 200 | `{"status": "already_exists", "activity": {...}}` |
| No recent run | 404 | Safe error detail |
| Invalid Garmin data | 502 | Safe error detail |
| Garmin access or SQLite unavailable | 503 | Safe error detail |

`activity` contains the six normalized fields described above. SQLite uses `external_activity_id` as a unique key; repeated or concurrent imports create one row, preserving the original record. Only normalized fields are stored, not raw Garmin responses or GPS/FIT data. The API shares the CLI's bounded recent-run selection. No frontend integration, analysis, or coaching is implemented.
