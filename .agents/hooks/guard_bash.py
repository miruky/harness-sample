#!/usr/bin/env python3
"""PreToolUse（Bash）: 取り返しのつかないコマンドと、秘密や実データに触るコマンドを実行前に止める。

文字列の照合なので、すり抜ける書き方は作れる。意図しない事故を減らすための柵であり、
外へ出さないための境界はサンドボックスと権限の設定が受け持つ。
"""

from __future__ import annotations

import re

from _common import block, read_input, record

RULES: list[tuple[str, str]] = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rR][a-zA-Z]*\s+(-[a-zA-Z]+\s+)*(/|~|\$HOME|\.\.|\.)(\s|$)",
     "広い範囲を消す rm は実行しません。消したいファイルを個別に指定してください。"),
    (r"\bgit\s+push\b",
     "push はエージェントから行いません。変更をコミットしたところで止め、人へ引き継いでください。"),
    (r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-zA-Z]*f|\bgit\s+checkout\s+(--\s+)?\.(\s|$)",
     "作業中の変更を捨てるコマンドは実行しません。戻したいファイルを個別に指定してください。"),
    (r"(^|[\s;&|(])(cat|less|head|tail|grep|sed|awk|cp|mv|source|\.)\s[^;&|]*\.env(?!\.example)(\.[\w-]+)?(\s|$)",
     ".env は読みません。必要な設定の名前は .env.example にあります。"),
    (r"bookings\.json",
     "bookings.json は実データです。動作を確かめるときは BOOKING_DB で一時ファイルを指定してください。"),
    (r"\b(curl|wget)\b[^|;]*\|\s*(ba|z)?sh\b",
     "取得したスクリプトをそのまま実行しません。"),
    (r"\bsudo\b",
     "sudo は使いません。"),
]  # fmt: skip


def main() -> None:
    event = read_input()
    command = str(event.get("tool_input", {}).get("command", ""))
    for pattern, message in RULES:
        if re.search(pattern, command):
            block(event, "guard_bash", f"止めました: {message}")
    record(event, "guard_bash", "pass")


if __name__ == "__main__":
    main()
