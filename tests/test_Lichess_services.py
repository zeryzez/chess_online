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
        return {'url': 'https://lichess.org/flakyid'}

    def always_fail(self, *args, **kwargs):
        raise ConnectionError("network down")

    def succeed(self, *args, **kwargs):
        return {'url': 'https://lichess.org/success'}

@pytest.fixture
def service(monkeypatch):
    # Instantiate service with dummy token
    svc = LichessService(token="fake_token")
    return svc

# Test extract_game_info
def test_extract_game_info_success():
    svc = LichessService(token="x")
    resp = {'url': 'https://lichess.org/abc123'}
    game_id, url = svc.extract_game_info(resp)
    assert game_id == 'abc123'
    assert url == resp['url']

def test_extract_game_info_missing_url():
    svc = LichessService(token="x")
    with pytest.raises(ValueError):
        svc.extract_game_info({})

# Test retry helper with a flaky function
def test_retry_flaky(monkeypatch, service):
    dummy = Dummy()
    # Call flaky via retry: should succeed on 3rd call
    result = service._retry(dummy.flaky)
    # Ensure the function was called three times
    assert dummy.call_count == 3
    assert result == {'url': 'https://lichess.org/flakyid'}

# Test retry helper aborts after max_retries
def test_retry_max_retries(monkeypatch, service):
    dummy = Dummy()
    # override initial backoff to speed up
    with pytest.raises(ConnectionError):
        service._retry(dummy.always_fail, max_retries=2, initial_backoff=0)
    assert dummy.call_count == 2

# Test challenge_bot integrates with retry
def test_challenge_bot(monkeypatch, service):
    # monkeypatch the create method to be flaky
    dummy = Dummy()
    monkeypatch.setattr(service.client.challenges, 'create', dummy.flaky)
    resp = service.challenge_bot('maia1', clock_limit=300, clock_increment=2)
    # Should have returned dict from flaky success
    assert 'url' in resp
    assert dummy.call_count == 3

# Test challenge_user
def test_challenge_user(monkeypatch, service):
    # always succeed
    monkeypatch.setattr(service.client.challenges, 'create', dummy_success := Dummy().succeed)
    resp = service.challenge_user('user1', clock_limit=120, clock_increment=1, rated=False)
    assert resp['url'] == 'https://lichess.org/success'

# Test create_seek
def test_create_seek(monkeypatch, service):
    # always succeed using board.create_seek
    monkeypatch.setattr(service.client.board, 'create_seek', dummy_success := Dummy().succeed)
    resp = service.create_seek(60, 0, rated=True, variant='standard')
    assert resp['url'] == 'https://lichess.org/success'
