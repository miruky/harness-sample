#!/usr/bin/env python3
"""PostToolUse（Edit、Write、apply_patch）: src/ の Python ファイルを編集したら、層の向きだけをその場で確かめる。

整形とリントはここでは行わない。import を足す前の書きかけの状態に反応して作業を何度も止め、
整形でファイルが書き換わると次の編集がやり直しになったため（docs/harness-log.md）。
整形とリントは、終了前のフック（verify_before_stop.py）が受け持つ。
"""

from __future__ import annotations

import subprocess

from _common import PROJECT, block, edited_paths, read_input, record


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=PROJECT, capture_output=True, text=True, timeout=60)


def main() -> None:
    event = read_input()
    targets = [
        relative
        for relative in edited_paths(event)
        if relative.endswith(".py")
        and relative.startswith("src/")
        and (PROJECT / relative).exists()
    ]
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
