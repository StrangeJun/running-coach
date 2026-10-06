# Intended architecture

The application uses `frontend/` (Next.js App Router) and `backend/app/` (FastAPI). No additional services are required for the MVP. See the root README for setup, API responses, and checks.

- `database.py`: SQLite connections and idempotent activity-table initialization.
- `activity_store.py`: normalized storage; unique `external_activity_id` prevents duplicates atomically and preserves the original row.
- `integrations/garmin.py`: saved-session access and Garmin response normalization into `activities.py`’s `NormalizedActivity`.
- `garmin_cli.py`: manual login/access check; no activity persistence.
- `main.py`: `/health` and `POST /api/garmin/import-latest`; coordinates Garmin retrieval and storage. Import uses saved tokens without interactive login.

Frontend API consumption, analysis, and coaching remain unimplemented. The boundaries below guide those future components.

```text
Garmin response → Garmin adapter → NormalizedActivity → activity storage
                                                     → analysis engine → coaching → next session
Frontend → FastAPI endpoints → application workflow
```

| Boundary | Responsibility |
| --- | --- |
| Garmin integration | Retrieve the latest running activity on explicit user request. Own authentication and Garmin-specific response handling behind an adapter/service boundary. |
| Activity normalization | Translate Garmin responses into an internal `NormalizedActivity` with explicit units and missing values. Downstream code must not depend on Garmin payloads or client libraries. |
| Persistence | Store normalized activities locally in SQLite. Keep database access separate from metric calculations. |
| Analysis engine | Calculate running metrics from normalized data using deterministic, testable domain functions independent of network, UI, and LLMs. |
| Coaching | Consume calculated metrics and relevant stored history to produce guidance and a next-session recommendation. Keep independent from UI; a future OpenAI integration belongs here. |
| Frontend | Next.js UI owns interaction and presentation, consumes backend APIs, and displays import status, analysis, and coaching. |

FastAPI coordinates import, normalization, storage, analysis, and coaching. Garmin-specific details stop at the adapter. LLMs explain and coach from calculated metrics; they do not calculate basic running metrics.

Choose concrete schemas and module layout when implementing the relevant task. Avoid speculative infrastructure or generalized provider frameworks.
