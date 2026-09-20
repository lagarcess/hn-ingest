"""In-process HN Firebase stand-in for pull tests (real HTTP, no mocks)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class FakeHNServer:
    def __init__(self, newstory_ids: list[int], items: dict[int, Any]) -> None:
        this = self
        self.newstory_ids = list(newstory_ids)
        self.items = dict(items)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args: object) -> None:
                return

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/newstories.json":
                    this._write(self, 200, this.newstory_ids)
                    return
                if self.path.startswith("/item/") and self.path.endswith(".json"):
                    raw_id = self.path[len("/item/") : -len(".json")]
                    try:
                        item_id = int(raw_id)
                    except ValueError:
                        this._write(self, 404, {"error": "bad id"})
                        return
                    this._write(self, 200, this.items.get(item_id))
                    return
                this._write(self, 404, {"error": "not found"})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @staticmethod
    def _write(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
        payload = json.dumps(body).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self) -> str:
        self._thread.start()
        return self.base_url

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)
