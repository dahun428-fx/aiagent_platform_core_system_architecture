"""Shared helpers for the impl/ services: the reference module, a small JSON HTTP server and client."""
from __future__ import annotations

import importlib.util
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 65536


def load_ref():
    """The reference module from examples/, loaded once and shared, so contracts and Fault are the same objects."""
    if "platform_ref" in sys.modules:
        return sys.modules["platform_ref"]
    spec = importlib.util.spec_from_file_location("platform_ref", ROOT / "examples/python/platform_ref.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform_ref"] = module
    spec.loader.exec_module(module)
    return module


class JsonHandler(BaseHTTPRequestHandler):
    """Base handler: quiet logs, bounded JSON bodies, JSON responses."""

    def log_message(self, *_):
        pass

    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > MAX_BODY:
            raise ValueError("invalid body size")
        return json.loads(self.rfile.read(size))

    def send_json(self, status, payload, content_type="application/json", headers=None):
        raw = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)


def serve(handler_class, port):
    """Bind to loopback only. port 0 lets the OS pick a free port."""
    return ThreadingHTTPServer(("127.0.0.1", port), handler_class)


def call_json(method, url, body=None, headers=None, timeout=5.0):
    """Return (status, headers, parsed JSON body). HTTP errors are returned, not raised."""
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, dict(response.headers), json.loads(response.read() or b"null")
    except HTTPError as exc:
        raw = exc.read()
        return exc.code, dict(exc.headers), json.loads(raw) if raw else None
    except (URLError, OSError) as exc:
        raise ConnectionError(str(exc)) from exc
