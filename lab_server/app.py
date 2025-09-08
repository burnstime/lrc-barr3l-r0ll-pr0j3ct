import os
import importlib
from typing import TYPE_CHECKING
from flask import Flask, render_template, request, session, jsonify
from werkzeug.utils import secure_filename

try:
    # optional server-side session support
    from flask_session import Session
    HAS_FLASK_SESSION = True
except Exception:
    HAS_FLASK_SESSION = False

# For type-checkers only; avoid real import at runtime to prevent
# editor/linter 'could not be resolved' if redis isn't installed in the
# workspace interpreter. The `type: ignore` silences missing-import errors.
if TYPE_CHECKING:
    import redis as _redis  # type: ignore[import]
import re
import secrets
import time
from urllib.parse import unquote_plus
from collections import defaultdict, deque
import importlib

# Optional Redis client for distributed rate-limiting / session stores
_redis_client = None
if os.environ.get('USE_REDIS_RATE_LIMIT', '0') == '1':
    try:
        _redis_client = importlib.import_module('redis')
        # create a client instance
        try:
            REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
            _redis_client = _redis_client.from_url(REDIS_URL)
        except Exception:
            # leave as module reference; attempt to construct on demand later
            pass
    except Exception:
        _redis_client = None

app = Flask(__name__)
# Use an explicit SECRET_KEY in production. Generate ephemeral key only when absent.
def _read_secret_file(name: str):
    path = f"/run/secrets/{name}"
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        pass
    return os.environ.get(name)

secret = _read_secret_file('SECRET_KEY')
if secret:
    app.secret_key = secret
else:
    # Ephemeral secret for development; log so operators set a persistent value.
    app.logger.warning('SECRET_KEY not set; generating ephemeral key. Set SECRET_KEY in production.')
    app.secret_key = secrets.token_hex(32)

# Cookie/security defaults. Allow override via env for testing.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '1') == '1'

# Limit upload size (bytes). Default 10 MB.
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', str(10 * 1024 * 1024)))

# Allowed upload extensions (comma-separated env or sensible defaults)
ALLOWED_EXTENSIONS = set([e.strip().lower() for e in os.environ.get('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg').split(',')])

# Simple in-memory rate limiting for /decode-login: N requests per WINDOW seconds per remote
app.config['DECODER_RATE_LIMIT'] = int(os.environ.get('DECODER_RATE_LIMIT', '30'))
app.config['DECODER_RATE_WINDOW'] = int(os.environ.get('DECODER_RATE_WINDOW', '60'))
# structure: {key: deque([timestamps])}
_decoder_attempts = defaultdict(deque)

# Read ADMIN_TOKEN from Docker secret if present
ADMIN_TOKEN = _read_secret_file('ADMIN_TOKEN')


def _send_alert(msg: str):
    """Simple alert sink: log and append to alerts.log in repo root."""
    app.logger.error(msg)
    try:
        # try webhook first
        try:
            from .alerting import send_webhook_alert
            if send_webhook_alert(msg):
                return
        except Exception:
            pass
        # prefer syslog if available
        try:
            import syslog
            syslog.syslog(syslog.LOG_ERR, msg)
            return
        except Exception:
            pass
        with open(os.path.join(os.getcwd(), 'alerts.log'), 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception as e:
        app.logger.debug(f'Failed to write alerts.log: {e}')


def _redis_rate_limited(client, key: str, limit: int, window: int) -> bool:
    """Atomic Redis rate limit using INCR and EXPIRE; returns True if limited."""
    try:
        # Lua script: incr the key, set expiry if this is the first increment, return count
        lua = (
            "local c = redis.call('INCR', KEYS[1])\n"
            "if c == 1 then redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1])) end\n"
            "return c"
        )
        # If client is a redis.StrictRedis or redis.Redis instance with eval
        cnt = client.eval(lua, 1, key, window)
        try:
            cnt = int(cnt)
        except Exception:
            cnt = 0
        return cnt > limit
    except Exception as e:
        app.logger.debug(f'Redis rate limit check failed: {e}')
        return False

# Optional server-side sessions using Redis. To enable, set environment
# variable USE_SERVER_SESSION=1 and REDIS_URL (e.g. redis://redis:6379/0)
if os.environ.get('USE_SERVER_SESSION', '0') == '1' and HAS_FLASK_SESSION:
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    try:
        # import redis at runtime (if present) rather than at module import
        _redis = importlib.import_module('redis')
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = _redis.from_url(redis_url)
        Session(app)
        app.logger.info('Server-side sessions enabled via Redis')
    except Exception as e:
        app.logger.warning(f'Failed to enable server-side sessions: {e}')
else:
    if os.environ.get('USE_SERVER_SESSION', '0') == '1':
        app.logger.warning('USE_SERVER_SESSION requested but Flask-Session not installed; falling back to client sessions')


# Simple WAF function
def waf_blocked(input_str):
    if not input_str:
        return False
    # WAF enabled via env, default enabled for safety
    if os.environ.get('WAF_ENABLED', '1') != '1':
        return False
    # Normalize: URL-decode and lower-case to avoid simple obfuscation
    try:
        check = unquote_plus(input_str)
    except Exception:
        check = input_str
    check = check.lower()
    patterns = [p.strip().lower() for p in os.environ.get('WAF_PATTERNS', '<script>,drop,evil').split(',')]
    for pat in patterns:
        # simple substring/regex match
        if re.search(pat, check, re.IGNORECASE):
            return True
    return False


def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


def check_csrf(token):
    return token == session.get('csrf_token')


# Generate every possible combination of login type, username, and password
usernames = ['user', 'admin', 'staff']
passwords = ['userpass', 'adminpass', 'staffpass']
CREDENTIALS = {}
for login_type in ['login', 'admin-login', 'staff-login']:
    CREDENTIALS[login_type] = {}
    # map each username to the corresponding password by index
    for u, p in zip(usernames, passwords):
        CREDENTIALS[login_type][u] = p


# Utility: list all combos
def all_login_combinations():
    combos = []
    for key in CREDENTIALS:
        for username, password in CREDENTIALS[key].items():
            combos.append((key, username, password))
    return combos


@app.route('/decode-login', methods=['GET', 'POST'])
def decode_login():
    # DECODE_ENABLED must be explicitly enabled in production
    if os.environ.get('DECODE_ENABLED', '0') != '1' and not app.testing:
        # pretend endpoint does not exist in production
        return ('', 404)

    # Stronger admin guard: require an ADMIN_TOKEN to be configured and
    # require the exact header value. If no ADMIN_TOKEN is configured we
    # hide the endpoint (return 404) so it cannot be discovered.
    admin_token_env = ADMIN_TOKEN or os.environ.get('ADMIN_TOKEN')
    if not admin_token_env:
        # hide endpoint when no admin token is configured
        app.logger.warning('Attempt to access decoder but no ADMIN_TOKEN configured')
        return ('', 404)

    provided = (
        request.headers.get('X-ADMIN-TOKEN')
        or request.headers.get('X-Admin-Token')
        or request.args.get('admin_token')
        or request.form.get('admin_token')
    )
    if provided != admin_token_env:
        app.logger.warning(f'Unauthorized decoder access attempt from {request.remote_addr}')
        _send_alert(f'Unauthorized decoder access attempt from {request.remote_addr}')
        return jsonify({"result": "forbidden"}), 403

    # Network restriction: only allow local or docker-internal addresses to use this endpoint.
    # This prevents the decoder from being called from the public network even with a token.
    remote = (request.remote_addr or '')
    allow_local = remote in ('127.0.0.1', '::1') or remote.startswith('172.') or remote.startswith('10.') or remote.startswith('192.168.')
    if not allow_local:
        app.logger.warning(f'Decoder access denied for non-local address {remote}')
        _send_alert(f'Decoder access denied for non-local address {remote}')
        return jsonify({"result": "forbidden"}), 403

    # Rate limiting: prefer Redis-backed counters for distributed safety
    remote = request.remote_addr or 'global'
    window = app.config['DECODER_RATE_WINDOW']
    limit = app.config['DECODER_RATE_LIMIT']
    key = f"decoder:{remote}"
    try:
        if _redis_client is not None:
            # Redis INCR with expiry
            cnt = _redis_client.incr(key)
            if cnt == 1:
                _redis_client.expire(key, window)
            if cnt > limit:
                app.logger.warning(f'Decoder rate limit exceeded for {remote} (redis)')
                # if repeated hits, send an alert
                if cnt % limit == 0:
                    _send_alert(f"Repeated decoder rate limit for {remote}, count={cnt}")
                return jsonify({"result": "rate_limited"}), 429
        else:
            # Fallback to in-memory deque
            now = time.time()
            q = _decoder_attempts[remote]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                app.logger.warning(f'Decoder rate limit exceeded for {remote} (memory)')
                if len(q) % limit == 0:
                    _send_alert(f"Repeated decoder rate limit for {remote} (memory), count={len(q)}")
                return jsonify({"result": "rate_limited"}), 429
            q.append(now)
    except Exception as e:
        app.logger.debug(f'Rate limiter failed: {e}; falling back to in-memory')

    # audit log
    app.logger.info(f'Decode attempt from {remote} for params username={request.args.get("username") or request.form.get("username")}')

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
    else:
        username = request.args.get('username', '')
        password = request.args.get('password', '')

    # Check all login types but do not return stored password values.
    for login_type, creds in CREDENTIALS.items():
        for user, pwd in creds.items():
            if username == user and password == pwd:
                return jsonify({"result": "match", "type": login_type, "username": username})
    return jsonify({"result": "invalid", "username": username})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        token = request.form.get('csrf_token', '')
        if waf_blocked(username):
            return "Blocked by WAF!"
        if not check_csrf(token):
            return "Invalid CSRF token!"
        if CREDENTIALS['login'].get(username) == password:
            return "Login successful!"
        else:
            return "Invalid credentials!"
    else:
        csrf_token = generate_csrf_token()
        return render_template('login.html', csrf_token=csrf_token)


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        token = request.form.get('csrf_token', '')
        if waf_blocked(username):
            return "Blocked by WAF!"
        if not check_csrf(token):
            return "Invalid CSRF token!"
        if CREDENTIALS['admin-login'].get(username) == password:
            return "Admin login successful!"
        else:
            return "Invalid admin credentials!"
    else:
        csrf_token = generate_csrf_token()
        return render_template('admin_login.html', csrf_token=csrf_token)


@app.route('/staff-login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        token = request.form.get('csrf_token', '')
        if waf_blocked(username):
            return "Blocked by WAF!"
        if not check_csrf(token):
            return "Invalid CSRF token!"
        if CREDENTIALS['staff-login'].get(username) == password:
            return "Staff login successful!"
        else:
            return "Invalid staff credentials!"
    else:
        csrf_token = generate_csrf_token()
        return render_template('staff_login.html', csrf_token=csrf_token)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        token = request.form.get('csrf_token', '')
        if not check_csrf(token):
            return "Invalid CSRF token!"
        if not file or file.filename == '':
            return "No file selected!"
        filename = secure_filename(file.filename)
        if not filename:
            return "Invalid filename!"
        if '.' in filename:
            ext = filename.rsplit('.', 1)[1].lower()
        else:
            ext = ''
        if ext not in ALLOWED_EXTENSIONS:
            return "File type not allowed!"
        if waf_blocked(filename):
            return "Blocked by WAF!"
        upload_dir = os.path.abspath(os.path.join(os.getcwd(), 'uploads'))
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        file.save(save_path)
        return "File uploaded!"
    else:
        csrf_token = generate_csrf_token()
        return render_template('upload.html', csrf_token=csrf_token)



@app.route('/')
def index():
    return 'Server is running'


if __name__ == '__main__':
    # default to port 8000 inside the container
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
