"""Internal activity contract, independent of Garmin responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NormalizedActivity(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)

    external_activity_id: str = Field(min_length=1)
    date: datetime  # UTC activity start time, not Garmin's local clock time.
    distance_m: float = Field(ge=0)
    duration_s: float = Field(ge=0)  # Garmin duration, not elapsedDuration.
    average_heart_rate_bpm: float | None = Field(default=None, gt=0)
    average_cadence_spm: float | None = Field(default=None, gt=0)
