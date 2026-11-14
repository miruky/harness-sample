#!/usr/bin/env python3
"""Stop: 終わる前に4つ確かめる。通っていなければ、終わらせずに理由を返す。

1. 最後の報告が日本語か。指示ファイルと設定に書いても英語の報告が残ったので、ここで確かめる
2. 人が確かめてから変えるファイルが、書き換わっていないか
3. 仕様を変えたのに、Confluence の写しへ書き込んでいないものがないか（同期を使っているときだけ）
4. 変更があれば、整形してから make check が通るか

整形と、自動で直せるリントの修正は黙って済ませる。モデルに頼まなくても機械で決まるため。
直らないまま回り続けないよう、1回の依頼の中で続けて止めるのは3回までにする。
3回止めても通らなければ、そのまま終わらせて人に判断を渡す。
"""

from __future__ import annotations

import hashlib
import json
import subprocess

from _common import PROJECT, block, read_input, record

MAX_BLOCKS = 3
# 人が確かめてから変えるファイル。編集ツールを止めるだけではシェル経由の変更が残るので、終わる前にも確かめる
HUMAN_OWNED = (".agents/hooks/", ".github/workflows/", ".claude/settings.json", ".codex/")


def written_in_japanese(message: str) -> bool:
    """短い返事やコードだけの返事は対象にせず、文章の報告だけを見る。"""
    letters = sum(1 for ch in message if ch.isalpha())
    if letters < 40:
        return True
    japanese = sum(1 for ch in message if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff")
    return japanese / letters > 0.2


def human_owned_changes(status: str) -> list[str]:
    paths = [line[3:].strip().strip('"') for line in status.splitlines()]
    changed = [p for p in paths if p.startswith(HUMAN_OWNED)]
    if "uv.lock" in paths and "pyproject.toml" not in paths:
        changed.append("uv.lock")
    return changed


def unsynced_specs() -> list[str]:
    """台帳がある（Confluence との同期を使っている）ときだけ、未反映の仕様を挙げる。"""
    ledger_file = PROJECT / "docs" / "specs" / ".sync.json"
    if not ledger_file.exists():
        return []
    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
    names = []
    for path in sorted((PROJECT / "docs" / "specs").glob("*.md")):
        name = f"docs/specs/{path.name}"
        if path.name == "README.md":
            continue
        if ledger.get(name, {}).get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            names.append(name)
    return names


def main() -> None:
    event = read_input()
    state_file = PROJECT / ".harness" / "logs" / f"stop-{event.get('session_id', 'unknown')}.json"
    # 止めた回数は、1回の依頼の中だけで数える。stop_hook_active が偽なら、新しい依頼の最初の終了
    resumed = bool(event.get("stop_hook_active"))
    blocks = json.loads(state_file.read_text())["blocks"] if resumed and state_file.exists() else 0

    def stop(message: str) -> None:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({"blocks": blocks + 1}))
        block(event, "verify_before_stop", message)

    message = str(event.get("last_assistant_message") or "")
    if blocks < MAX_BLOCKS and not written_in_japanese(message):
        stop("報告が日本語になっていません。同じ内容を日本語で書き直してください。")

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=PROJECT, capture_output=True, text=True
    )
    if not status.stdout.strip():
        return  # 何も変えていない応答（質問への回答など）では検査しない

    owned = human_owned_changes(status.stdout)
    if owned and blocks < MAX_BLOCKS:
        stop(
            "人が確かめてから変えるファイルが書き換わっています: "
            + ", ".join(owned)
            + "\n人から頼まれた変更でなければ git checkout で元に戻し、変えたい内容を返答に書いてください。"
        )

    specs = unsynced_specs()
    if specs and blocks < MAX_BLOCKS:
        stop(
            "仕様が Confluence に反映されていません: "
            + ", ".join(specs)
            + "\n/sync-specs の手順で書き込み、台帳に記録してから終えてください。"
        )

    subprocess.run(["make", "format"], cwd=PROJECT, capture_output=True, text=True, timeout=120)
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

    tail = (check.stdout + check.stderr).strip()[-3000:]
    stop("make check が通っていません。出力を読んで直してから終えてください。\n\n" + tail)


if __name__ == "__main__":
    main()
