# Running Coach

Personal Garmin running analysis and coaching web application.

Core flow: Garmin → adapter → NormalizedActivity → storage → deterministic analysis → coaching → next training recommendation.

- Before substantial work, read [docs/AI/README.md](docs/AI/README.md) and follow its routing guide.
- Do not over-engineer; make the smallest reasonable change.
- Keep Garmin integration separate from analysis and coaching independent from UI.
- Never commit credentials, Garmin tokens, FIT files, GPS data, or personal activity data.
- Run relevant tests before considering work complete.
- Update `docs/AI/current_status.md` when project state materially changes.
