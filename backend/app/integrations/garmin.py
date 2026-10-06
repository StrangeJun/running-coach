"""Personal-use Garmin access. No database, UI, analysis, or coaching dependencies."""

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from garminconnect import Garmin, GarminConnectAuthenticationError
from pydantic import ValidationError

from app.activities import NormalizedActivity

DEFAULT_TOKEN_DIRECTORY = Path(__file__).resolve().parents[3] / ".garminconnect"

RUNNING_TYPES = {
    "running", "trail_running", "treadmill_running", "track_running",
    "street_running", "indoor_running", "ultra_run", "virtual_run",
}


class GarminAccessError(RuntimeError):
    """Safe public authentication, transport, or token-storage failure."""


class GarminDataError(RuntimeError):
    """Safe public error for unexpected Garmin response data."""


def normalize_run(activity: dict[str, Any]) -> NormalizedActivity:
    try:
        identifier = activity["activityId"]
        if isinstance(identifier, bool) or not isinstance(identifier, (str, int)):
            raise ValueError("Invalid activity id")
        if not str(identifier).strip() or (isinstance(identifier, int) and identifier <= 0):
            raise ValueError("Invalid activity id")
        timestamp = activity["startTimeGMT"]
        if not isinstance(timestamp, str) or len(timestamp) < 19:
            raise ValueError("Invalid start time")
        date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        heart_rate = activity.get("averageHR")
        cadence = activity.get("averageRunningCadenceInStepsPerMinute")
        # Garmin may use numeric zero when a sensor did not record data.
        if type(heart_rate) in (int, float) and heart_rate == 0:
            heart_rate = None
        if type(cadence) in (int, float) and cadence == 0:
            cadence = None
        return NormalizedActivity(
            external_activity_id=str(identifier), date=date.astimezone(timezone.utc),
            distance_m=activity["distance"], duration_s=activity["duration"],
            average_heart_rate_bpm=heart_rate,
            average_cadence_spm=cadence,
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        raise GarminDataError("Garmin returned invalid running activity fields.") from None


class GarminClient:
    def __init__(
        self,
        token_directory: Path,
        *,
        credential_provider: Callable[[], tuple[str, str]] | None = None,
        prompt_mfa: Callable[[], str] | None = None,
    ) -> None:
        self.token_directory = token_directory.expanduser()
        self.credential_provider = credential_provider
        self.prompt_mfa = prompt_mfa

    def _login(self) -> Garmin:
        tokenstore = str(self.token_directory)
        session = Garmin()
        try:
            session.login(tokenstore)
        except GarminConnectAuthenticationError:
            if self.credential_provider is None:
                raise GarminAccessError("Garmin login required; supply credentials locally.") from None
            try:
                email, password = self.credential_provider()
                session = Garmin(email, password, prompt_mfa=self.prompt_mfa)
                session.login(tokenstore)
            except Exception:
                raise GarminAccessError("Garmin login failed; check credentials or MFA locally.") from None
        except Exception:
            raise GarminAccessError("Garmin session access failed; retry later.") from None
        try:
            # login() suppresses persistence errors; make token reuse failure explicit.
            session.client.dump(tokenstore)
        except Exception:
            raise GarminAccessError("Could not save the Garmin session locally.") from None
        return session

    def latest_run(self, *, limit: int = 50) -> NormalizedActivity | None:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        session = self._login()
        try:
            activities = session.get_activities(0, limit, activitytype="running")
            # Persist any refresh that occurred during the request.
            session.client.dump(str(self.token_directory))
        except Exception:
            raise GarminAccessError("Could not retrieve Garmin activities or save the session.") from None
        if not isinstance(activities, list):
            raise GarminDataError("Garmin returned an unexpected activity list.")
        runs = []
        for activity in activities:
            if not isinstance(activity, dict) or not isinstance(activity.get("activityType"), dict):
                raise GarminDataError("Garmin returned an unexpected activity entry.")
            if activity["activityType"].get("typeKey") in RUNNING_TYPES:
                runs.append(normalize_run(activity))
        return max(runs, key=lambda run: run.date, default=None)
