#!/usr/bin/env python3
"""Generate an ADMIN HMAC header value compatible with lab_server.verify_admin_hmac.

Outputs: ts:nonce:hmac
Usage: ADMIN_HMAC_SECRET=secret python tools/generate_admin_hmac.py
"""
import os
import sys
import time
import secrets
import hmac
import hashlib

secret = os.environ.get('ADMIN_HMAC_SECRET')
if not secret:
    print('ADMIN_HMAC_SECRET not set', file=sys.stderr)
    sys.exit(2)

ts = str(int(time.time()))
nonce = secrets.token_hex(8)
msg = f"{ts}:{nonce}".encode('utf-8')
sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
print(f"{ts}:{nonce}:{sig}")
