# Backend focus

- Keep FastAPI endpoints thin; coordinate work through focused application functions/services.
- Keep persistence and transaction handling outside domain calculations.
- Enforce the Garmin adapter boundary described in `../../architecture.md`.
- Validate API inputs and normalized data; define useful failure responses.
- Test domain logic, persistence behavior, and changed API paths with synthetic data and mocked external calls.
