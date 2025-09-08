import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

RECORD_FILE = 'tools/alerts_received.jsonl'

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length)
        try:
            obj = json.loads(body)
        except Exception:
            obj = {'raw': body.decode('utf-8', errors='ignore')}
        with open(RECORD_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj) + '\n')
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    server = HTTPServer(('127.0.0.1', port), Handler)
    print('Alert server listening on', port)
    server.serve_forever()
