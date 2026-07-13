#!/bin/bash
# Start the Modal worker upload receiver on a specific port.
# Workers in Modal sandboxes upload artifacts via curl PUT to this server.
# Usage: ./start-upload-receiver.sh [port=19999]
#
# The receiver writes to absolute paths on the host filesystem.
# Workers use: curl -X PUT --data-binary @file -H "X-Token: $TOKEN" \
#   http://<HOST_IP>:<PORT>/absolute/path/to/destination

PORT="${1:-19999}"
TOKEN="gs-$(openssl rand -hex 8)"
echo "TOKEN=${TOKEN}" > /tmp/upload-token.txt
echo "PORT=${PORT}" >> /tmp/upload-token.txt

# Ensure firewall allows the port
ufw allow "${PORT}/tcp" comment "modal-worker-upload" 2>/dev/null || true

python3 -u -c "
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
TOKEN = open('/tmp/upload-token.txt').read().split()[0].split('=')[1]
class H(BaseHTTPRequestHandler):
    def do_PUT(self):
        if self.headers.get('X-Token') != TOKEN:
            self.send_response(403); self.end_headers(); return
        length = int(self.headers.get('Content-Length', 0))
        path = self.path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = self.rfile.read(length)
        with open(path, 'wb') as f: f.write(data)
        self.send_response(200); self.end_headers()
        self.wfile.write(b'ok:' + str(len(data)).encode())
    def do_GET(self):
        self.send_response(200); self.end_headers()
        path = self.path
        if os.path.exists(path): self.wfile.write(open(path,'rb').read())
        else: self.wfile.write(b'NOT_FOUND')
    def log_message(self, *a): pass
HTTPServer(('0.0.0.0', $PORT), H).serve_forever()
"
