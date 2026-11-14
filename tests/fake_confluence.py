"""Confluence の REST API のうち、docs_sync.py が使う3つだけをまねるサーバー。テスト専用。"""

from __future__ import annotations

import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeConfluence:
    def __init__(self) -> None:
        self.pages: dict[str, dict] = {}
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:
                return

            def reply(self, payload: dict) -> None:
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def payload(self) -> dict:
                return json.loads(self.rfile.read(int(self.headers["Content-Length"])))

            def do_GET(self) -> None:
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                page = fake.pages.get(query["title"][0])
                self.reply({"results": [page] if page else []})

            def do_POST(self) -> None:
                self.reply(fake.store(self.payload(), 1, str(len(fake.pages) + 1)))

            def do_PUT(self) -> None:
                payload = self.payload()
                page_id = self.path.rsplit("/", 1)[1]
                self.reply(fake.store(payload, payload["version"]["number"], page_id))

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def store(self, payload: dict, version: int, page_id: str) -> dict:
        # 本物と同じように、保存した本文は整形されて返ってくるものとして、タグの間に改行を入れる
        value = payload["body"]["storage"]["value"].replace("><", ">\n<")
        page = {
            "id": page_id,
            "title": payload["title"],
            "version": {"number": version},
            "body": {"storage": {"value": value}},
        }
        self.pages[payload["title"]] = page
        return page

    def edit_on_screen(self, title: str, old: str, new: str) -> None:
        """Confluence の画面で、誰かが本文を書き換えた状態を作る。"""
        storage = self.pages[title]["body"]["storage"]
        storage["value"] = storage["value"].replace(old, new)

    def close(self) -> None:
        self.server.shutdown()
