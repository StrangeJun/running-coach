"""Local SQLite connections and idempotent schema initialization."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect_database(path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect_database(path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                external_activity_id TEXT PRIMARY KEY NOT NULL,
                date TEXT NOT NULL,
                distance_m REAL NOT NULL CHECK (distance_m >= 0),
                duration_s REAL NOT NULL CHECK (duration_s >= 0),
                average_heart_rate_bpm REAL CHECK (average_heart_rate_bpm > 0),
                average_cadence_spm REAL CHECK (average_cadence_spm > 0)
            )
        """)
