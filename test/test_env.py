from _ebcf_alexa import env
from unittest.mock import patch, call
import pytest


@pytest.yield_fixture
def mock_now():
    with patch.object(env, 'now') as now:
        yield now


@patch('datetime.datetime')
def test_now_is_utc(fake_datetime):
    assert env.now()
    assert fake_datetime.now.call_args == call(tz=env.UTC)


def test_local_now(mock_now):
    assert env.localnow() == mock_now.return_value.astimezone.return_value
    assert mock_now.return_value.astimezone.call_args == call(env.TZ)


def test_date(mock_now):
    assert env.date() == mock_now.return_value.date.return_value


def test_local_date():
    with patch.object(env, 'localnow') as ln:
        assert env.localdate() == ln.return_value.date.return_value

