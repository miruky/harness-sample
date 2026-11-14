"""フックの共通処理。入力の読み取りと、あとで数えるための記録。

Claude Code と Codex は、フックへ渡す JSON の形がほぼ同じなので、同じスクリプトを両方から呼ぶ。
違うのはファイル編集の入力だけで、Claude Code は file_path、Codex は apply_patch のパッチ本文で届く。
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)
LOG = PROJECT / ".harness" / "logs" / "hooks.jsonl"


def read_input() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def edited_paths(event: dict[str, Any]) -> list[str]:
    """編集の対象になったファイルを、リポジトリのルートからの相対パスで返す。"""
    tool_input = event.get("tool_input", {})
    raw: list[str] = []
    if isinstance(tool_input, dict) and tool_input.get("file_path"):
        raw.append(str(tool_input["file_path"]))
    else:
        text = json.dumps(tool_input, ensure_ascii=False).replace("\\n", "\n")
        raw.extend(PATCH_FILE.findall(text))
    paths = []
    for item in raw:
        path = Path(item.strip().rstrip('"'))
        if not path.is_absolute():
            path = Path(str(event.get("cwd") or PROJECT)) / path
        try:
            paths.append(path.resolve().relative_to(PROJECT.resolve()).as_posix())
        except ValueError:
            paths.append(path.as_posix())
    return paths


def record(event: dict[str, Any], hook: str, outcome: str, detail: str = "") -> None:
    """フックが何をしたかを1行で残す。tools/harness_stats.py がこの記録を数える。"""
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session": event.get("session_id", ""),
        "event": event.get("hook_event_name", ""),
        "hook": hook,
        "tool": event.get("tool_name", ""),
        "outcome": outcome,
        "detail": detail[:300],
    }
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def block(event: dict[str, Any], hook: str, message: str) -> None:
    """終了コード2で止める。標準エラーの文章が、そのままエージェントへ渡る。"""
    record(event, hook, "block", message)
    print(message, file=sys.stderr)
    sys.exit(2)
