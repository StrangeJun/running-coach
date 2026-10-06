"""Persist normalized activities without depending on Garmin response formats."""

from datetime import datetime
from pathlib import Path

from app.activities import NormalizedActivity
from app.database import connect_database


def store_activity(path: Path, activity: NormalizedActivity) -> tuple[NormalizedActivity, bool]:
    """Return the stored activity and whether a new row was inserted.

    Duplicate IDs preserve the original record. The unique key and atomic
    insert protect against duplicate rows from concurrent import requests.
    """
    with connect_database(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO activities (
                external_activity_id, date, distance_m, duration_s,
                average_heart_rate_bpm, average_cadence_spm
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (external_activity_id) DO NOTHING
            """,
            (
                activity.external_activity_id, activity.date.isoformat(),
                activity.distance_m, activity.duration_s,
                activity.average_heart_rate_bpm, activity.average_cadence_spm,
            ),
        )
        imported = cursor.rowcount == 1
        row = connection.execute(
            "SELECT * FROM activities WHERE external_activity_id = ?",
            (activity.external_activity_id,),
        ).fetchone()
        fields = dict(row)
        fields["date"] = datetime.fromisoformat(fields["date"])
        stored = NormalizedActivity(**fields)
    return stored, imported
