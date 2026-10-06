# Project context

Running Coach is a personal-use web application for analyzing Garmin runs and providing personalized coaching. The current target user is the owner.

## Intended user workflow

Garmin Watch → Garmin Connect → user clicks “Import Latest Run” → backend retrieves the latest running activity → normalize → store locally → deterministic analysis → personalized coaching → recommend the next training session.

## MVP scope

- Next.js, TypeScript, and Tailwind CSS frontend.
- Python/FastAPI backend with SQLite persistence.
- Personal-use Garmin integration, manually triggered import, calculated running metrics, and a simple coaching/recommendation path.

## Future direction

Add OpenAI API coaching based on calculated metrics. Consider official Garmin Activity API integration later.

## Current non-goals

Background polling, official Garmin Activity API integration, multi-user operation, and a complex training platform. See `current_status.md` for current delivery scope.
