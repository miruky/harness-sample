#!/usr/bin/env python3
"""PostToolUse（Edit、Write、apply_patch）: 編集した Python ファイルを整形し、リントと層の検査の結果をすぐ返す。

整形は黙って直す。直せない指摘だけを標準エラーへ出し、終了コード2でエージェントへ渡す。
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
        and relative.startswith(("src/", "tests/", "tools/"))
        and (PROJECT / relative).exists()
    ]
    if not targets:
        return

    run("uv", "run", "ruff", "format", *targets)
    run("uv", "run", "ruff", "check", "--fix", "--quiet", *targets)
    problems: list[str] = []
    lint = run("uv", "run", "ruff", "check", "--output-format", "concise", *targets)
    if lint.returncode != 0:
        problems.append(lint.stdout.strip())
    if any(relative.startswith("src/") for relative in targets):
        layers = run("uv", "run", "python", "tools/check_layers.py")
        if layers.returncode != 0:
            problems.append(layers.stdout.strip())
    if problems:
        detail = "\n\n".join(problems)
        block(event, "check_edit", f"編集後の検査で指摘があります。直してください。\n\n{detail}")
    record(event, "check_edit", "pass", ", ".join(targets))


if __name__ == "__main__":
    main()
