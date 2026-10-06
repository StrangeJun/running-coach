import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from app.activities import NormalizedActivity
from app.activity_store import store_activity
from app.database import initialize_database


def synthetic_run(identifier="synthetic-123", **changes):
    return NormalizedActivity(
        external_activity_id=identifier,
        date=datetime(2026, 10, 6, 7, tzinfo=timezone.utc),
        distance_m=5000.5, duration_s=1800.0,
        **changes,
    )


def rows(database):
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT * FROM activities").fetchall()


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "coach.sqlite3"
    initialize_database(path)
    return path


def test_stores_normalized_fields_and_optional_nulls(database):
    run = synthetic_run()
    stored, imported = store_activity(database, run)
    assert imported is True
    assert stored == run
    assert rows(database) == [("synthetic-123", "2026-10-06T07:00:00+00:00", 5000.5, 1800.0, None, None)]


def test_stores_sensor_values(database):
    run = synthetic_run(average_heart_rate_bpm=145.0, average_cadence_spm=172.0)
    stored, imported = store_activity(database, run)
    assert imported is True
    assert stored == run
    assert rows(database)[0][-2:] == (145.0, 172.0)


def test_duplicate_keeps_original_row_even_if_metrics_change(database):
    original = synthetic_run()
    store_activity(database, original)
    changed = original.model_copy(update={"distance_m": 6000.0, "average_heart_rate_bpm": 150.0})
    stored, imported = store_activity(database, changed)
    assert imported is False
    assert stored == original
    assert len(rows(database)) == 1


def test_initialization_and_duplicate_import_preserve_data_across_restarts(database):
    run = synthetic_run()
    store_activity(database, run)
    initialize_database(database)
    stored, imported = store_activity(database, run)
    assert imported is False
    assert stored == run
    assert len(rows(database)) == 1


def test_different_ids_create_distinct_rows(database):
    for identifier in ["synthetic-1", "synthetic-2"]:
        assert store_activity(database, synthetic_run(identifier))[1] is True
    assert len(rows(database)) == 2


def test_identifier_is_parameterized(database):
    identifier = "synthetic'); DROP TABLE activities; --"
    run = synthetic_run(identifier)
    assert store_activity(database, run)[0] == run
    assert rows(database)[0][0] == identifier


def test_concurrent_duplicate_imports_create_exactly_one_row(database):
    run = synthetic_run()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: store_activity(database, run), range(4)))
    assert sum(imported for _, imported in results) == 1
    assert all(stored == run for stored, _ in results)
    assert len(rows(database)) == 1
