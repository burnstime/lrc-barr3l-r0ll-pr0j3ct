import os
import sys
import re
import io
# ensure repo root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lab_server.app import app, all_login_combinations


def report(title, ok, details=""):
    print(f"== {title} ==")
    print("PASS" if ok else "FAIL")
    if details:
        print(details)
    print()


def run():
    with app.test_client() as c:
        # Ensure decoder endpoint is enabled for this local probe and set a known admin token
        # so the probe can exercise admin-token gated functionality when running outside container.
        os.environ.setdefault('DECODE_ENABLED', '1')
        os.environ.setdefault('ADMIN_TOKEN', 'rt-secret')

        # 1) Decoder brute-force info disclosure
        combos = all_login_combinations()
        matches = []
        for login_type, user, pwd in combos[:50]:
            resp = c.get('/decode-login', query_string={'username': user, 'password': pwd})
            data = resp.get_json() or {}
            if data.get('result') == 'match':
                matches.append((login_type, user))
        report('Decoder brute-force (sample)', len(matches) > 0, f"Found matches: {matches[:10]}")

        # 2) CSRF: ensure POST without token fails, with token succeeds when creds correct
        get_resp = c.get('/login')
        html = get_resp.get_data(as_text=True)
        m = re.search(r'name=[\'\"]csrf_token[\'\"].*?value=[\'\"]([^\'\"]+)[\'\"]', html)
        token = m.group(1) if m else None
        resp_no_token = c.post('/login', data={'username': 'user', 'password': 'userpass'})
        ok_no_token = b'Invalid CSRF token' in resp_no_token.get_data() or b'Invalid CSRF' in resp_no_token.get_data()
        ok_with_token = False
        if token:
            resp_token = c.post('/login', data={'username': 'user', 'password': 'userpass', 'csrf_token': token})
            ok_with_token = b'Login successful' in resp_token.get_data()
        report('CSRF enforcement', ok_no_token and ok_with_token, f"token_present={bool(token)}, without_token_resp={resp_no_token.get_data()[:100]}, with_token_resp={resp_token.get_data()[:100] if token else b''}")

        # 3) WAF blocking
        # get token for post
        token2 = token or None
        payload = '<script>alert(1)</script>'
        resp_waf = c.post('/login', data={'username': payload, 'password': 'x', 'csrf_token': token2})
        waf_blocked = b'Blocked by WAF' in resp_waf.get_data()
        report('WAF blocking of script tag', waf_blocked, f"response={resp_waf.get_data()}")

        # 4) Upload handling: forbidden extension then allowed extension
        get_up = c.get('/upload')
        html_up = get_up.get_data(as_text=True)
        m2 = re.search(r'name=[\'\"]csrf_token[\'\"].*?value=[\'\"]([^\'\"]+)[\'\"]', html_up)
        up_token = m2.group(1) if m2 else token2

        # forbidden ext
        data = {
            'csrf_token': up_token,
            'file': (io.BytesIO(b'abc'), 'evil.exe')
        }
        resp_forbidden = c.post('/upload', data=data, content_type='multipart/form-data')
        forbidden_ok = b'File type not allowed' in resp_forbidden.get_data()

        # allowed ext
        data_ok = {
            'csrf_token': up_token,
            'file': (io.BytesIO(b'abc'), 'test.txt')
        }
        resp_ok = c.post('/upload', data=data_ok, content_type='multipart/form-data')
        ok_saved = b'File uploaded' in resp_ok.get_data()

        # check saved file exists
        upload_dir = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
        saved_exists = False
        try:
            saved_exists = os.path.exists(os.path.join(upload_dir, 'test.txt'))
        except Exception:
            saved_exists = False

        report('Upload handling', forbidden_ok and ok_saved and saved_exists, f"forbidden_resp={resp_forbidden.get_data()[:120]}, ok_resp={resp_ok.get_data()[:120]}, saved_exists={saved_exists}, upload_dir={upload_dir}")

        # 5) Admin token enforcement
        # set env token and retry
        os.environ['ADMIN_TOKEN'] = 'rt-secret'
        # call without token
        resp_no_admin = c.get('/decode-login', query_string={'username': 'user', 'password': 'staffpass'})
        no_admin_forbidden = resp_no_admin.status_code == 403
        # call with header
        resp_with_admin = c.get('/decode-login', headers={'X-ADMIN-TOKEN': 'rt-secret'}, query_string={'username': 'user', 'password': 'staffpass'})
        with_admin_ok = resp_with_admin.status_code == 200 and (resp_with_admin.get_json().get('result') in ('match','invalid'))
        report('Admin-token enforcement', no_admin_forbidden and with_admin_ok, f"no_admin_status={resp_no_admin.status_code}, with_admin_status={resp_with_admin.status_code}, with_admin_json={resp_with_admin.get_json()}")

        # --- Extended checks ---
        # 6) Password discovery (brute via decode-login with admin token)
        pw_candidates = ['userpass', 'adminpass', 'staffpass', 'password', '123456']
        found = {}
        for u in ['user', 'admin', 'staff']:
            for pw in pw_candidates:
                resp = c.get('/decode-login', headers={'X-ADMIN-TOKEN': 'rt-secret'}, query_string={'username': u, 'password': pw})
                j = resp.get_json() or {}
                if j.get('result') == 'match':
                    found[u] = pw
                    break
        report('Password discovery via decoder', len(found) == 3, f"found={found}")

        # 7) WAF bypass attempts (encoding/obfuscation)
        waf_payloads = [
            '<script>alert(1)</script>',
            '%3Cscript%3Ealert(1)%3C%2Fscript%3E',
            '<scr' + 'ipt>alert(1)</scr' + 'ipt>',
            '\u003Cscript\u003Ealert(1)\u003C/script\u003E',
            '<ScRipT>alert(1)</ScRipT>'
        ]
        waf_results = {}
        for p in waf_payloads:
            resp = c.post('/login', data={'username': p, 'password': 'x', 'csrf_token': token})
            waf_results[p] = 'Blocked' if b'Blocked by WAF' in resp.get_data() else 'Passed'
        report('WAF bypass variants', all(v == 'Blocked' for v in waf_results.values()), f"results={waf_results}")

        # 8) Upload path traversal attempts
        traversal_names = ['../../secret.txt', '..\\..\\secret.txt', '.../../secret.txt', 'normal.txt']
        trav_results = {}
        for name in traversal_names:
            data = {'csrf_token': up_token, 'file': (io.BytesIO(b'test'), name)}
            resp = c.post('/upload', data=data, content_type='multipart/form-data')
            trav_results[name] = resp.get_data()[:200]
        report('Upload traversal attempts', all(b'Invalid filename' not in v and b'File uploaded' in v for v in trav_results.values()), f"results={trav_results}")

        # 9) CSRF token replay: token from one session cannot be used in another
        with app.test_client() as c1:
            r1 = c1.get('/login')
            m1 = re.search(r'name=[\'\"]csrf_token[\'\"].*?value=[\'\"]([^\'\"]+)[\'\"]', r1.get_data(as_text=True))
            t1 = m1.group(1) if m1 else None
        with app.test_client() as c2:
            # attempt to use t1 in a different client session
            r2 = c2.post('/login', data={'username': 'user', 'password': 'userpass', 'csrf_token': t1})
            replay_allowed = b'Login successful' in r2.get_data()
        report('CSRF replay across sessions', not replay_allowed, f"replay_allowed={replay_allowed}, response={r2.get_data()}")


if __name__ == '__main__':
    run()
