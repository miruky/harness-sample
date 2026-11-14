"""ハーネス自体の検査。指示ファイルや設定が、古くなったり壊れたりしていないかを確かめる。

  uv run python tools/check_harness.py

確かめること:
  - AGENTS.md と CLAUDE.md が決めた行数に収まっている（長くなると守られにくくなるため）
  - 指示ファイルやスキルがパスで挙げたファイルが、実際に存在する
  - .claude/settings.json が JSON として正しく、フックのスクリプトが存在して実行できる
  - スキルとサブエージェントに name と description がある
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINE_BUDGET = {"AGENTS.md": 60, "CLAUDE.md": 30}
DESCRIPTION_LIMIT = 1536  # Claude Code がスキルの一覧に載せる説明の上限（文字）
PATH_PATTERN = re.compile(r"`([\w./-]+\.(?:md|py|json|toml|yml|yaml|sh))`|\]\(([\w./-]+\.md)\)")


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    block = text[4 : text.index("\n---", 4)]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def check_budgets() -> list[str]:
    problems = []
    for name, budget in LINE_BUDGET.items():
        path = ROOT / name
        if not path.exists():
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > budget:
            problems.append(
                f"{name}: {lines} 行あります（上限 {budget} 行）。"
                "直し方: 手順は .claude/skills/、特定の場所だけの決まりは .claude/rules/、"
                "詳しい説明は docs/ へ移し、ここには1行の案内だけ残してください。"
            )
    return problems


def check_references() -> list[str]:
    problems = []
    sources = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
    sources += sorted((ROOT / ".claude").rglob("*.md"))
    sources += sorted((ROOT / ".agents").rglob("*.md"))
    for source in sources:
        if not source.exists():
            continue
        for match in PATH_PATTERN.finditer(source.read_text(encoding="utf-8")):
            target = match.group(1) or match.group(2)
            # ディレクトリを含む書き方だけを確かめる。cli.py のような短い呼び名は対象にしない
            if "/" not in target or target.startswith("http") or "*" in target or "<" in target:
                continue
            candidates = [ROOT / target, source.parent / target]
            if not any(candidate.exists() for candidate in candidates):
                where = source.relative_to(ROOT)
                problems.append(
                    f"{where}: `{target}` が見つかりません。"
                    "直し方: 移動や改名に合わせて書き直すか、不要になった行を消してください。"
                )
    return problems


def check_settings() -> list[str]:
    problems = []
    path = ROOT / ".claude" / "settings.json"
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f".claude/settings.json: 読めません（{error}）"]
    for event, groups in settings.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                command = hook.get("command", "")
                for script in re.findall(r"\.agents/hooks/[\w.-]+", command):
                    target = ROOT / script
                    if not target.exists():
                        problems.append(f"{event}: {script} がありません")
                    elif not os.access(target, os.X_OK):
                        problems.append(f"{event}: {script} に実行権限がありません（chmod +x）")
    return problems


def check_skills_and_agents() -> list[str]:
    problems = []
    files = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
    files += sorted((ROOT / ".claude" / "agents").glob("*.md"))
    for path in files:
        fields = frontmatter(path)
        where = path.relative_to(ROOT)
        for key in ("name", "description"):
            if not fields.get(key):
                problems.append(f"{where}: frontmatter に {key} がありません")
        if len(fields.get("description", "")) > DESCRIPTION_LIMIT:
            problems.append(f"{where}: description が {DESCRIPTION_LIMIT} 文字を超えています")
    return problems


def main() -> int:
    problems = check_budgets() + check_references() + check_settings() + check_skills_and_agents()
    for problem in problems:
        print(problem)
    if problems:
        print(f"\n{len(problems)} 件の指摘があります。")
        return 1
    print("ハーネスの検査: 指摘なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
