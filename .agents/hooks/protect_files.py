#!/usr/bin/env python3
"""PreToolUse（Edit、Write、apply_patch）: 手で書き換えないファイルへの編集を止める。"""

from __future__ import annotations

from _common import block, edited_paths, read_input, record

PROTECTED: dict[str, str] = {
    "uv.lock": "uv.lock は手で編集しません。依存を変えるときは uv add か uv remove を使ってください。",
    ".env": ".env は編集しません。項目を増やすときは .env.example に名前だけ足してください。",
    "bookings.json": "bookings.json は実データです。編集しません。",
    ".claude/settings.json": "権限とフックの設定は人が確認してから変えます。変えたい内容を返答に書いてください。",
}  # fmt: skip
PROTECTED_DIRS: dict[str, str] = {
    ".agents/hooks": "フックの変更は人が確認してから行います。変えたい内容を提案として返答に書いてください。",
    ".github/workflows": "CIの変更は人が確認してから行います。変えたい内容を提案として返答に書いてください。",
}  # fmt: skip


def reason_to_block(relative: str) -> str | None:
    if relative == ".env.example":
        return None
    for name, message in PROTECTED.items():
        if relative == name or relative.startswith(f"{name}."):
            return message
    for directory, message in PROTECTED_DIRS.items():
        if relative.startswith(f"{directory}/"):
            return message
    return None


def main() -> None:
    event = read_input()
    for relative in edited_paths(event):
        message = reason_to_block(relative)
        if message:
            block(event, "protect_files", f"止めました: {message}")
    record(event, "protect_files", "pass")


if __name__ == "__main__":
    main()
