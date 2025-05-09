# tests/test_game_controller.py

import pytest
from requests.exceptions import Timeout, ConnectionError
from berserk.exceptions import ResponseError
from services.lichess_service import LichessService

# Dummy functions to simulate behavior
class Dummy:
    def __init__(self):
        self.call_count = 0

    def flaky(self, *args, **kwargs):
        # first two calls fail, then succeed
        self.call_count += 1
        if self.call_count < 3:
            raise Timeout("timeout occurred")
        return {'id': 'flakyid'}  # now return id key

    def always_fail(self, *args, **kwargs):
        self.call_count += 1
        raise ConnectionError("network down")

    def succeed(self, *args, **kwargs):
        return {'id': 'success'}

@pytest.fixture
def service():
    # Instantiate service with dummy token
    return LichessService(token="fake_token")

# Test extract_game_info

def test_extract_game_info_success():
    svc = LichessService(token="x")
    resp = {'id': 'abc123'}
    game_id, url = svc.extract_game_info(resp)
    assert game_id == 'abc123'
    assert url == 'https://lichess.org/abc123'


def test_extract_game_info_missing_id():
    svc = LichessService(token="x")
    with pytest.raises(ValueError):
        svc.extract_game_info({})

# Test retry helper with a flaky function

def test_retry_flaky(service):
    dummy = Dummy()
    result = service._retry(dummy.flaky)
    assert dummy.call_count == 3
    assert result == {'id': 'flakyid'}

# Test retry helper aborts after max_retries

def test_retry_max_retries(service):
    dummy = Dummy()
    with pytest.raises(ConnectionError):
        service._retry(dummy.always_fail, max_retries=2, initial_backoff=0)
    assert dummy.call_count == 2

# Test challenge_bot integrates with retry

def test_challenge_bot(monkeypatch, service):
    dummy = Dummy()
    monkeypatch.setattr(service.client.challenges, 'create_ai', dummy.flaky)
    resp = service.challenge_bot(level=1, clock_limit=300, clock_increment=2)
    assert 'id' in resp
    assert dummy.call_count == 3

# Test challenge_user integrates with retry

def test_challenge_user(monkeypatch, service):
    dummy = Dummy()
    monkeypatch.setattr(service.client.challenges, 'create', dummy.succeed)
    resp = service.challenge_user('user1', clock_limit=120, clock_increment=1, rated=False)
    assert resp == {'id': 'success'}

# Test create_seek integrates with retry

def test_create_seek(monkeypatch, service):
    dummy = Dummy()
    # service.create_seek uses client.challenges.create_open
    monkeypatch.setattr(service.client.challenges, 'create_open', dummy.succeed)
    resp = service.create_seek(clock_limit=60, clock_increment=0, rated=True, variant='standard')
    assert resp == {'id': 'success'}
