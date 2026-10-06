from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError

from app.integrations.garmin import GarminClient, GarminAccessError, GarminDataError


def activity(identifier=123, date="2026-10-06 07:00:00", kind="running", **changes):
    return {
        "activityId": identifier, "startTimeGMT": date,
        "activityType": {"typeKey": kind}, "distance": 5000.5, "duration": 1800.0,
        "averageHR": 145.0, "averageRunningCadenceInStepsPerMinute": 172.0,
        **changes,
    }


@pytest.fixture
def sdk():
    with patch("app.integrations.garmin.Garmin", autospec=True) as factory:
        session = factory.return_value
        session.client = MagicMock()
        session.get_activities.return_value = [activity()]
        yield factory, session


def test_reuses_tokens_without_requesting_credentials(tmp_path, sdk):
    factory, session = sdk
    credentials = MagicMock(side_effect=AssertionError("Must reuse session"))
    result = GarminClient(tmp_path, credential_provider=credentials).latest_run()
    credentials.assert_not_called()
    session.login.assert_called_once_with(str(tmp_path))
    assert result.model_dump() == {
        "external_activity_id": "123", "date": datetime(2026, 10, 6, 7, tzinfo=timezone.utc),
        "distance_m": 5000.5, "duration_s": 1800.0,
        "average_heart_rate_bpm": 145.0, "average_cadence_spm": 172.0,
    }


def test_first_login_uses_credentials_and_saves_session(tmp_path, sdk):
    factory, resumed = sdk
    resumed.login.side_effect = GarminConnectAuthenticationError("Missing session")
    fresh = MagicMock(spec=Garmin)
    fresh.client = MagicMock()
    fresh.get_activities.return_value = [activity()]
    factory.side_effect = [resumed, fresh]
    credentials = MagicMock(return_value=("synthetic@example.test", "synthetic-password"))
    mfa = MagicMock(return_value="000000")
    result = GarminClient(tmp_path, credential_provider=credentials, prompt_mfa=mfa).latest_run()
    assert result.external_activity_id == "123"
    credentials.assert_called_once_with()
    factory.assert_called_with("synthetic@example.test", "synthetic-password", prompt_mfa=mfa)
    fresh.login.assert_called_once_with(str(tmp_path))
    fresh.client.dump.assert_called_with(str(tmp_path))


@pytest.mark.parametrize("error", [GarminConnectConnectionError, GarminConnectTooManyRequestsError])
def test_network_or_rate_limit_does_not_retry_with_credentials(tmp_path, sdk, error):
    _, session = sdk
    session.login.side_effect = error("private upstream response")
    credentials = MagicMock()
    with pytest.raises(GarminAccessError) as caught:
        GarminClient(tmp_path, credential_provider=credentials).latest_run()
    assert "private upstream response" not in str(caught.value)
    credentials.assert_not_called()


def test_invalid_session_without_credentials_has_safe_error(tmp_path, sdk):
    _, session = sdk
    session.login.side_effect = GarminConnectAuthenticationError("secret")
    with pytest.raises(GarminAccessError, match="login"):
        GarminClient(tmp_path).latest_run()


def test_most_recent_run_selected_by_time_not_list_position(tmp_path, sdk):
    _, session = sdk
    session.get_activities.return_value = [
        activity(1, "2026-10-01 07:00:00"),
        activity(2, "2026-10-07 07:00:00", "cycling"),
        activity(3, "2026-10-06 07:00:00", "trail_running"),
    ]
    assert GarminClient(tmp_path).latest_run().external_activity_id == "3"
    session.get_activities.assert_called_once_with(0, 50, activitytype="running")


@pytest.mark.parametrize("payload", [[], [activity(kind="cycling")]])
def test_no_recent_run_returns_none(tmp_path, sdk, payload):
    _, session = sdk
    session.get_activities.return_value = payload
    assert GarminClient(tmp_path).latest_run() is None


@pytest.mark.parametrize("kind", ["running", "trail_running", "treadmill_running", "track_running", "street_running", "indoor_running", "ultra_run", "virtual_run"])
def test_running_variants(tmp_path, sdk, kind):
    _, session = sdk
    session.get_activities.return_value = [activity(kind=kind)]
    assert GarminClient(tmp_path).latest_run().external_activity_id == "123"


@pytest.mark.parametrize("sensor", [None, 0])
def test_missing_sensor_values_remain_none(tmp_path, sdk, sensor):
    _, session = sdk
    session.get_activities.return_value = [activity(averageHR=sensor, averageRunningCadenceInStepsPerMinute=sensor)]
    result = GarminClient(tmp_path).latest_run()
    assert result.average_heart_rate_bpm is None
    assert result.average_cadence_spm is None


@pytest.mark.parametrize("changes", [
    {"activityId": None}, {"startTimeGMT": "bad-date"}, {"distance": -1},
    {"duration": None}, {"averageHR": -1}, {"distance": float("nan")},
    {"distance": True}, {"startTimeGMT": None}, {"averageHR": False}, {"averageHR": ""},
])
def test_malformed_run_rejected_without_payload_leak(tmp_path, sdk, changes):
    _, session = sdk
    session.get_activities.return_value = [activity(**changes, activityName="private-name")]
    with pytest.raises(GarminDataError) as caught:
        GarminClient(tmp_path).latest_run()
    assert "private-name" not in str(caught.value)


@pytest.mark.parametrize("payload", [{"unexpected": "private"}, [None], [{"activityType": None}]])
def test_malformed_activity_list_has_safe_error(tmp_path, sdk, payload):
    _, session = sdk
    session.get_activities.return_value = payload
    with pytest.raises(GarminDataError):
        GarminClient(tmp_path).latest_run()


def test_fetch_failure_is_sanitized(tmp_path, sdk):
    _, session = sdk
    session.get_activities.side_effect = GarminConnectConnectionError("private response")
    with pytest.raises(GarminAccessError) as caught:
        GarminClient(tmp_path).latest_run()
    assert "private response" not in str(caught.value)


def test_session_save_failure_is_reported(tmp_path, sdk):
    _, session = sdk
    session.client.dump.side_effect = OSError("private token path")
    with pytest.raises(GarminAccessError, match="session"):
        GarminClient(tmp_path).latest_run()


@pytest.mark.parametrize("limit", [0, -1, 101, True])
def test_invalid_limit_rejected_before_network(tmp_path, sdk, limit):
    _, session = sdk
    with pytest.raises(ValueError):
        GarminClient(tmp_path).latest_run(limit=limit)
    session.login.assert_not_called()
