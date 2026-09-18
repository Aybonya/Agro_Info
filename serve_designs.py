import http.server
import socketserver
import threading
import os
import sys

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class HandlerModern(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

class HandlerLegacy(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/legacy_admin.html'
        return super().do_GET()

def start_server(port, handler_class):
    # Allow port reuse immediately
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler_class) as httpd:
        print(f"[READY] Server started on http://localhost:{port}")
        httpd.serve_forever()

if __name__ == '__main__':
    t1 = threading.Thread(target=start_server, args=(3000, HandlerModern), daemon=True)
    t2 = threading.Thread(target=start_server, args=(3001, HandlerLegacy), daemon=True)
    t1.start()
    t2.start()
    print("Both servers running:\n- Modern Cyber-AgTech Design: http://localhost:3000\n- Classic AgroFlow ERP Design: http://localhost:3001")
    sys.stdout.flush()
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("Stopping servers...")
