"""Serve only the distributable, on localhost, with correct WASM MIME type."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
dist = Path(__file__).resolve().parent.parent / "dist"

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm"}
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(dist)))
print(f"Doom: http://localhost:{args.port} — Ctrl+C to stop", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
