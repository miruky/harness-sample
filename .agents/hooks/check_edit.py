#!/usr/bin/env python3
"""PostToolUse（Edit、Write、Bash、apply_patch）: src/ の Python ファイルが変わっていたら、層の向きをその場で確かめる。

編集ツールだけを見張っても足りない。エージェントはシェルのコマンドでもファイルを書き換えるので、
Bash のあとにも、変更されたファイルを git から拾って確かめる（docs/harness-log.md）。
整形とリントはここでは行わず、終了前のフック（verify_before_stop.py）が受け持つ。
"""

from __future__ import annotations

import subprocess

from _common import PROJECT, block, edited_paths, read_input, record


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=PROJECT, capture_output=True, text=True, timeout=60)


def changed_sources() -> list[str]:
    """コミットしていない変更のうち、src/ の Python ファイル。"""
    done = run("git", "status", "--porcelain", "--", "src")
    return [line[3:] for line in done.stdout.splitlines() if line.endswith(".py")]


def main() -> None:
    event = read_input()
    if event.get("tool_name") == "Bash":
        targets = changed_sources()
    else:
        targets = [p for p in edited_paths(event) if p.endswith(".py") and p.startswith("src/")]
    if not targets:
        return

    problems: list[str] = []
    layers = run("uv", "run", "python", "tools/check_layers.py")
    if layers.returncode != 0:
        problems.append(layers.stdout.strip())
    if problems:
        detail = "\n\n".join(problems)
        block(event, "check_edit", f"層の向きの検査で指摘があります。直してください。\n\n{detail}")
    record(event, "check_edit", "pass", ", ".join(targets))


if __name__ == "__main__":
    main()
