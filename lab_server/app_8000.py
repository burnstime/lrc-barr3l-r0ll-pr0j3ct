from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
import re
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# Use server-side session for reliability in tests
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
Session(app)


# Simple WAF function
def waf_blocked(input_str):
    if not input_str:
        return False
    patterns = [r"<script>", r"DROP", r"evil"]
    for pat in patterns:
        if re.search(pat, input_str, re.IGNORECASE):
            return True
    return False


def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


def check_csrf(token):
    return token == session.get('csrf_token')


# Generate credential mapping: map each username to its corresponding password
usernames = ['user', 'admin', 'staff']
passwords = ['userpass', 'adminpass', 'staffpass']
CREDENTIALS = {}
for login_type in ['login', 'admin-login', 'staff-login']:
    CREDENTIALS[login_type] = {}
    # Map username -> corresponding password using zip to avoid accidental overwrites
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
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
    else:
        username = request.args.get('username', '')
        password = request.args.get('password', '')
    # Check all login types
    for login_type, creds in CREDENTIALS.items():
        for user, pwd in creds.items():
            if username == user and password == pwd:
                # do not return stored password values in responses
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
        filename = file.filename
        if waf_blocked(filename):
            return "Blocked by WAF!"
        # Save file logic here (omitted)
        return "File uploaded!"
    else:
        csrf_token = generate_csrf_token()
        return render_template('upload.html', csrf_token=csrf_token)



@app.route('/')
def index():
    return 'Server is running'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
