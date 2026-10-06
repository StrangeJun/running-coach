import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_initializes_database_and_reports_ready(tmp_path):
    database = tmp_path / "nested" / "coach.sqlite3"
    with TestClient(create_app(database)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert database.is_file()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_database_persists_across_restarts(tmp_path):
    database = tmp_path / "coach.sqlite3"
    with TestClient(create_app(database)):
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE scaffold_test (value TEXT)")
            connection.execute("INSERT INTO scaffold_test VALUES ('synthetic')")
    with TestClient(create_app(database)) as client:
        assert client.get("/health").status_code == 200
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM scaffold_test").fetchall() == [("synthetic",)]


def test_health_reports_database_failure_without_exposing_path(tmp_path):
    database = tmp_path / "coach.sqlite3"
    with TestClient(create_app(database)) as client:
        database.unlink()
        database.mkdir()
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_database_path_can_be_configured_by_environment(tmp_path, monkeypatch):
    database = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("RUNNING_COACH_DB_PATH", str(database))
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
    assert database.is_file()
