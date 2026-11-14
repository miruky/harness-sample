"""Atlassian のMCPサーバーのうち、仕様の同期で使う5つのツールだけをまねるサーバー。計測用。

標準入出力で JSON-RPC をやり取りする。ページは MOCK_CONFLUENCE_STATE のファイルに保存する。
  claude --mcp-config tests/mock-mcp.json --strict-mcp-config
"""

from __future__ import annotations

import difflib
import json
import os
import sys
from pathlib import Path
from typing import Any

STATE = Path(os.environ.get("MOCK_CONFLUENCE_STATE", ".harness/mock-confluence.json"))


def load() -> dict[str, Any]:
    if STATE.exists():
        state: dict[str, Any] = json.loads(STATE.read_text(encoding="utf-8"))
        return state
    return {"pages": {}}


def save(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def tool(name: str, description: str, properties: dict[str, str], required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {key: {"type": kind} for key, kind in properties.items()},
            "required": required,
        },
    }


TOOLS = [
    tool("createConfluenceContent", "ページを作る。ページIDと版を返す",
         {"title": "string", "body": "string"}, ["title", "body"]),
    tool("updateConfluenceContent", "ページの本文を置き換える。新しい版を返す",
         {"pageId": "string", "body": "string"}, ["pageId", "body"]),
    tool("getConfluenceContent", "ページの題名、版、本文の全文を返す",
         {"pageId": "string"}, ["pageId"]),
    tool("listConfluenceContentVersions", "ページの版の番号を新しい順に返す。本文は返さない",
         {"pageId": "string"}, ["pageId"]),
    tool("diffConfluenceContentVersions", "2つの版の本文の差分だけを返す",
         {"pageId": "string", "fromVersion": "integer", "toVersion": "integer"},
         ["pageId", "fromVersion", "toVersion"]),
]  # fmt: skip


def call(name: str, args: dict[str, Any]) -> str:
    state = load()
    pages = state["pages"]
    if name == "createConfluenceContent":
        page_id = str(100 + len(pages) + 1)
        pages[page_id] = {"title": args["title"], "versions": [args["body"]]}
        save(state)
        return json.dumps({"pageId": page_id, "version": 1}, ensure_ascii=False)
    page = pages[str(args["pageId"])]
    if name == "updateConfluenceContent":
        page["versions"].append(args["body"])
        save(state)
        return json.dumps({"pageId": args["pageId"], "version": len(page["versions"])})
    if name == "getConfluenceContent":
        return json.dumps(
            {
                "title": page["title"],
                "version": len(page["versions"]),
                "body": page["versions"][-1],
            },
            ensure_ascii=False,
        )
    if name == "listConfluenceContentVersions":
        return json.dumps({"versions": list(range(len(page["versions"]), 0, -1))})
    old = page["versions"][int(args["fromVersion"]) - 1].splitlines()
    new = page["versions"][int(args["toVersion"]) - 1].splitlines()
    return "\n".join(difflib.unified_diff(old, new, lineterm="", n=0))


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        message = json.loads(line)
        method, request_id = message.get("method"), message.get("id")
        if request_id is None:
            continue
        if method == "initialize":
            result: dict[str, Any] = {
                "protocolVersion": message["params"].get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mock-confluence", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = message["params"]
            text = call(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": text}]}
        else:
            result = {}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
