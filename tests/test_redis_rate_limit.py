import os
import pytest
import importlib


@pytest.mark.skipif('REDIS_URL' not in os.environ and True, reason='No REDIS_URL configured')
def test_redis_rate_limit_integration():
    # This test expects a reachable Redis server at REDIS_URL
    try:
        redis = importlib.import_module('redis')
    except Exception:
        pytest.skip('redis library not available')
    url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    try:
        r = redis.from_url(url)
        # simple ping
        r.ping()
    except Exception:
        pytest.skip('Redis not reachable')
    # enable redis rate limiter
    os.environ['USE_REDIS_RATE_LIMIT'] = '1'
    # ensure ADMIN_TOKEN is set so protected endpoint is accessible
    os.environ['ADMIN_TOKEN'] = os.environ.get('ADMIN_TOKEN', 'tt')
    app = importlib.import_module('lab_server.app').app
    client = app.test_client()
    # clear key for test remote
    key = 'decoder:127.0.0.1'
    try:
        r.delete(key)
    except Exception:
        pass
    limit = int(app.config.get('DECODER_RATE_LIMIT', 5))
    exceeded = False
    for i in range(limit + 2):
        resp = client.get('/decode-login', query_string={'username': 'no', 'password': 'no'}, headers={'X-ADMIN-TOKEN': os.environ.get('ADMIN_TOKEN','')})
        if resp.status_code == 429:
            exceeded = True
            break
    assert exceeded
