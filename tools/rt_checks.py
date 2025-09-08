#!/usr/bin/env python3
import re
import requests
from pathlib import Path

BASE = "http://127.0.0.1:8000"

def get_csrf(session, path="/login"):
    r = session.get(BASE + path)
    r.raise_for_status()
    m = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
    return m.group(1) if m else None


def check_decode(admin_token_path=None):
    s = requests.Session()
    r = s.get(BASE + '/decode-login')
    print('decode_no_header:', r.status_code, r.text.strip())
    if admin_token_path and Path(admin_token_path).exists():
        token = Path(admin_token_path).read_text().strip()
        r2 = s.get(BASE + '/decode-login', headers={'X-Admin-Token': token})
        print('decode_with_admin:', r2.status_code, r2.text.strip())
    else:
        print('decode_with_admin: admin token not found')


def check_login_and_csrf_replay():
    s1 = requests.Session()
    t1 = get_csrf(s1, '/login')
    print('session1 csrf:', t1 is not None)
    r1 = s1.post(BASE + '/login', data={'username': 'user', 'password': 'userpass', 'csrf_token': t1})
    print('login_post session1:', r1.status_code, r1.text.strip())

    s2 = requests.Session()
    t2 = get_csrf(s2, '/login')
    print('session2 csrf:', t2 is not None)
    # attempt replay: use t1 (from session1) against session2
    r_replay = s2.post(BASE + '/login', data={'username': 'user', 'password': 'userpass', 'csrf_token': t1})
    print('csrf_replay attempt:', r_replay.status_code, r_replay.text.strip())


def check_uploads():
    s = requests.Session()
    csrf = get_csrf(s, '/upload')
    if not csrf:
        # try login page token as fallback
        csrf = get_csrf(s, '/login')
    print('upload csrf token found:', csrf is not None)
    # disallowed .exe
    files = {'file': ('evil.exe', b'MZFAKE', 'application/octet-stream')}
    data = {'csrf_token': csrf}
    r_exe = s.post(BASE + '/upload', files=files, data=data)
    print('upload .exe:', r_exe.status_code, r_exe.text.strip())
    # allowed .txt
    files = {'file': ('hello.txt', b'hello', 'text/plain')}
    r_txt = s.post(BASE + '/upload', files=files, data=data)
    print('upload .txt:', r_txt.status_code, r_txt.text.strip())


if __name__ == '__main__':
    print('=== decode checks ===')
    check_decode(admin_token_path='..\\secrets\\ADMIN_TOKEN')
    print('\n=== login & csrf replay ===')
    check_login_and_csrf_replay()
    print('\n=== uploads ===')
    check_uploads()
