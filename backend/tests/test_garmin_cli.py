from unittest.mock import patch

from app.garmin_cli import main
from app.integrations.garmin import GarminAccessError, GarminDataError, normalize_run


def test_cli_outputs_only_normalized_fields(tmp_path, capsys):
    run = normalize_run({
        "activityId": 456, "startTimeGMT": "2026-10-06 07:00:00", "distance": 3000,
        "duration": 1200, "activityName": "private-name", "startLatitude": 37.0,
    })
    with patch("app.garmin_cli.GarminClient", autospec=True) as client:
        client.return_value.latest_run.return_value = run
        assert main(["--token-dir", str(tmp_path), "--limit", "10"]) == 0
        client.return_value.latest_run.assert_called_once_with(limit=10)
    import json
    output = json.loads(capsys.readouterr().out)
    assert set(output) == {"external_activity_id", "date", "distance_m", "duration_s", "average_heart_rate_bpm", "average_cadence_spm"}
    assert output["date"] == "2026-10-06T07:00:00Z"
    assert output["average_heart_rate_bpm"] is None


def test_cli_no_run_reports_window_and_nonzero_exit(capsys):
    with patch("app.garmin_cli.GarminClient", autospec=True) as client:
        client.return_value.latest_run.return_value = None
        assert main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "recent" in captured.err


def test_cli_safe_errors_have_no_traceback(capsys):
    for error in [GarminAccessError("Garmin access failed."), GarminDataError("Invalid activity data.")]:
        with patch("app.garmin_cli.GarminClient", autospec=True) as client:
            client.return_value.latest_run.side_effect = error
            assert main([]) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Traceback" not in captured.err


def test_cli_login_cancelled(capsys):
    with patch("app.garmin_cli.GarminClient", autospec=True) as client:
        client.return_value.latest_run.side_effect = KeyboardInterrupt
        assert main([]) == 1
    assert "cancelled" in capsys.readouterr().err


def test_cli_rejects_invalid_limit_before_access():
    import pytest
    with patch("app.garmin_cli.GarminClient", autospec=True) as client:
        with pytest.raises(SystemExit) as caught:
            main(["--limit", "0"])
        assert caught.value.code == 2
        client.assert_not_called()
