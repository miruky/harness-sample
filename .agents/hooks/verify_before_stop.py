#!/usr/bin/env python3
"""Stop: 変更があるのに全検査が通っていなければ、終わらせずに結果を返す。

直らないまま回り続けないよう、同じセッションで続けて止めるのは3回までにする。
3回止めても通らなければ、そのまま終わらせて人に判断を渡す。
"""

from __future__ import annotations

import json
import subprocess

from _common import PROJECT, block, read_input, record

MAX_BLOCKS = 3


def main() -> None:
    event = read_input()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=PROJECT, capture_output=True, text=True
    )
    if not status.stdout.strip():
        return  # 何も変えていない応答（質問への回答など）では検査しない

    state_file = PROJECT / ".harness" / "logs" / f"stop-{event.get('session_id', 'unknown')}.json"
    blocks = json.loads(state_file.read_text())["blocks"] if state_file.exists() else 0

    check = subprocess.run(
        ["make", "check"], cwd=PROJECT, capture_output=True, text=True, timeout=300
    )
    if check.returncode == 0:
        record(event, "verify_before_stop", "pass")
        state_file.unlink(missing_ok=True)
        return
    if blocks >= MAX_BLOCKS:
        record(event, "verify_before_stop", "give_up", "make check が通らないまま終了")
        print(json.dumps({"systemMessage": "make check が通っていません。人の確認が必要です。"}))
        return

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"blocks": blocks + 1}))
    tail = (check.stdout + check.stderr).strip()[-3000:]
    block(
        event,
        "verify_before_stop",
        "make check が通っていません。出力を読んで直してから終えてください。\n\n" + tail,
    )


if __name__ == "__main__":
    main()
