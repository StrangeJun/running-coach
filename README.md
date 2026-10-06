# Running Coach

Personal Garmin running analysis and coaching. The current scaffold has a static Next.js landing page and a FastAPI health endpoint backed by local SQLite. Garmin import and activity storage are not implemented.

## Local setup

Requirements: Node.js 20.9+ and Python 3.10+ (verified with Node 24 and Python 3.14).

Backend, from the repository root:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`GET http://127.0.0.1:8000/health` checks SQLite connectivity; API docs are at `/docs`. Startup creates `data/running_coach.sqlite3` at the repository root. Set `RUNNING_COACH_DB_PATH` in the backend environment to override it; relative paths resolve from the working directory. Database files remain local and ignored. No activity schema is created yet.

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
