# Intended architecture

The target boundaries below guide future implementation. The scaffold uses `frontend/` (Next.js App Router) and `backend/app/` (FastAPI). `backend/app/database.py` owns SQLite connections; startup creates the local database, and `/health` checks connectivity. No activity schema or frontend API consumption exists yet. See the root README for setup and checks. No additional services are required for the MVP.

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
