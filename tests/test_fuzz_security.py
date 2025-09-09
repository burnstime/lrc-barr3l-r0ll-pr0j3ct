from hypothesis import given, strategies as st
import io
# os and json intentionally unused in some fuzz fixtures; keep if needed

from lab_server.app import app


@given(username=st.text(min_size=0, max_size=100), password=st.text(min_size=0, max_size=100))
def test_fuzz_decode(username, password):
    client = app.test_client()
    # Use testing mode
    app.testing = True
    resp = client.get('/decode-login', query_string={'username': username, 'password': password})
    # Decode endpoint returns JSON or 404; ensure no server error
    assert resp.status_code in (200, 404, 403, 429)


@given(filename=st.text(min_size=0, max_size=100), content=st.binary(max_size=1024))
def test_fuzz_upload(filename, content):
    client = app.test_client()
    app.testing = True
    data = {
        'file': (io.BytesIO(content), filename or 'fuzz.bin')
    }
    resp = client.post('/upload', data=data, content_type='multipart/form-data')
    # either handled or rejected; never 500
    assert resp.status_code != 500
