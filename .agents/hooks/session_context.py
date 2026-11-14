#!/usr/bin/env python3
"""SessionStart: いまのブランチ、未コミットの変更、進行中の計画を、最初に見える場所へ出す。"""

from __future__ import annotations

import subprocess

from _common import PROJECT, read_input, record


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], cwd=PROJECT, capture_output=True, text=True)
    return done.stdout.strip()


def main() -> None:
    event = read_input()
    lines = [f"ブランチ: {git('branch', '--show-current') or '(なし)'}"]
    changed = git("status", "--short")
    lines.append("未コミットの変更:\n" + changed if changed else "未コミットの変更: なし")
    plans = sorted(
        p.name for p in (PROJECT / "docs" / "plans").glob("*.md") if p.name != "README.md"
    )
    if plans:
        lines.append("進行中の計画: " + ", ".join(f"docs/plans/{name}" for name in plans))
    print("\n".join(lines))
    record(event, "session_context", "pass")


if __name__ == "__main__":
    main()
