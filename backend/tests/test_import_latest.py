import sqlite3
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.activities import NormalizedActivity
from app.integrations.garmin import GarminAccessError, GarminClient, GarminDataError
from app.main import create_app, get_garmin_client


@pytest.fixture
def run():
    return NormalizedActivity(
        external_activity_id="synthetic-456",
        date=datetime(2026, 10, 6, 7, tzinfo=timezone.utc),
        distance_m=5000.0, duration_s=1800.0,
        average_heart_rate_bpm=145.0, average_cadence_spm=None,
    )


@pytest.fixture
def api(tmp_path, run):
    database = tmp_path / "coach.sqlite3"
    garmin = MagicMock(spec=GarminClient)
    garmin.latest_run.return_value = run
    app = create_app(database)
    app.dependency_overrides[get_garmin_client] = lambda: garmin
    with TestClient(app) as client:
        yield client, garmin, database


def activity_count(database):
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT COUNT(*) FROM activities").fetchone()[0]


def test_import_latest_returns_created_and_stores_activity(api, run):
    client, garmin, database = api
    response = client.post("/api/garmin/import-latest")
    assert response.status_code == 201
    assert response.json() == {"status": "imported", "activity": run.model_dump(mode="json")}
    garmin.latest_run.assert_called_once_with()
    assert activity_count(database) == 1


def test_repeat_import_reports_existing_and_does_not_overwrite(api, run):
    client, garmin, database = api
    assert client.post("/api/garmin/import-latest").status_code == 201
    garmin.latest_run.return_value = run.model_copy(update={"distance_m": 7000.0})
    response = client.post("/api/garmin/import-latest")
    assert response.status_code == 200
    assert response.json() == {"status": "already_exists", "activity": run.model_dump(mode="json")}
    assert activity_count(database) == 1


def test_duplicate_detection_survives_application_restart(tmp_path, run):
    database = tmp_path / "coach.sqlite3"
    for expected_status in [201, 200]:
        app = create_app(database)
        garmin = MagicMock(spec=GarminClient)
        garmin.latest_run.return_value = run
        app.dependency_overrides[get_garmin_client] = lambda: garmin
        with TestClient(app) as client:
            assert client.post("/api/garmin/import-latest").status_code == expected_status
    assert activity_count(database) == 1


def test_no_recent_run_returns_404_without_storing(api):
    client, garmin, database = api
    garmin.latest_run.return_value = None
    response = client.post("/api/garmin/import-latest")
    assert response.status_code == 404
    assert response.json() == {"detail": "No recent running activity found"}
    assert activity_count(database) == 0


@pytest.mark.parametrize("error,status", [(GarminAccessError, 503), (GarminDataError, 502)])
def test_garmin_failure_is_sanitized_and_does_not_store(api, error, status):
    client, garmin, database = api
    garmin.latest_run.side_effect = error("private Garmin response")
    response = client.post("/api/garmin/import-latest")
    assert response.status_code == status
    assert "private Garmin response" not in response.text
    assert activity_count(database) == 0


def test_database_write_failure_is_sanitized(api):
    client, _, database = api
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE activities")
    response = client.post("/api/garmin/import-latest")
    assert response.status_code == 503
    assert response.json() == {"detail": "Activity storage unavailable"}


def test_startup_and_health_do_not_contact_garmin(tmp_path):
    with patch("app.main.GarminClient", autospec=True) as factory:
        with TestClient(create_app(tmp_path / "coach.sqlite3")) as client:
            assert client.get("/health").status_code == 200
        factory.assert_not_called()


def test_api_client_uses_token_directory_without_credential_prompts(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNNING_COACH_GARMIN_TOKEN_DIR", str(tmp_path))
    with patch("app.main.GarminClient", autospec=True) as factory:
        client = get_garmin_client()
    factory.assert_called_once_with(tmp_path)
    assert client == factory.return_value


def test_get_does_not_import(api):
    client, garmin, database = api
    assert client.get("/api/garmin/import-latest").status_code == 405
    garmin.latest_run.assert_not_called()
    assert activity_count(database) == 0
