import sys
import os
import time
sys.path.insert(0, r'C:\Users\12265\OneDrive\Documents')
from lab_server.app import app


def test_admin_token_required():
    app.testing = True
    client = app.test_client()
    # set ADMIN_TOKEN so tests exercise header-based auth
    os.environ['ADMIN_TOKEN'] = 'tt'
    r = client.get('/decode-login', headers={'X-ADMIN-TOKEN': 'tt'}, query_string={'username': 'user', 'password': 'userpass'})
    assert r.status_code == 200

    # ensure 403 without header when token set
    r2 = client.get('/decode-login', query_string={'username': 'user', 'password': 'userpass'})
    assert r2.status_code == 403
    # with header
    r3 = client.get('/decode-login', headers={'X-ADMIN-TOKEN': 'tt'}, query_string={'username': 'user', 'password': 'userpass'})
    assert r3.status_code == 200


def test_decoder_rate_limit_memory():
    # force in-memory limiter
    if 'USE_REDIS_RATE_LIMIT' in os.environ:
        del os.environ['USE_REDIS_RATE_LIMIT']
    # ensure ADMIN_TOKEN is set for protected endpoint
    os.environ['ADMIN_TOKEN'] = os.environ.get('ADMIN_TOKEN', 'tt')
    app.testing = True
    client = app.test_client()
    # clear in-memory attempts if present
    try:
        import importlib
        lab_module = importlib.import_module('lab_server.app')
        lab_module._decoder_attempts.clear()
    except Exception:
        pass
    # hit the endpoint more than limit
    limit = int(app.config.get('DECODER_RATE_LIMIT', 10))
    for i in range(limit + 2):
        r = client.get('/decode-login', query_string={'username': 'no', 'password': 'no'})
        if i < limit:
            assert r.status_code in (200, 200)
        else:
            assert r.status_code == 429
            break
