"""docs/specs/ の仕様と、Confluence の写しの対応を、手元の台帳で管理する。

APIが届かない環境では、Confluence への書き込みと取得をエージェントがMCPのツールで行う。
このスクリプトは外へ通信せず、
「どのファイルを書き込む必要があるか」「ページの本文を取得する必要があるか」を、台帳だけで答える。
モデルにページの全文を取得させる回数を減らすのが目的。

  uv run python tools/specs_sync.py status                 # 書き込みが要るファイルを挙げる
  uv run python tools/specs_sync.py payload <ファイル>    # 書き込む本文（末尾に sha256）を出す
  uv run python tools/specs_sync.py record <ファイル> <ページID> <版>  # 書き込んだら記録する
  uv run python tools/specs_sync.py check <ファイル> <いまの版>        # 本文の取得が要るか

台帳は docs/specs/.sync.json。ファイルごとに sha256、ページID、最後に書き込んだ版を持つ。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "docs" / "specs"
LEDGER = SPECS / ".sync.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load() -> dict[str, dict[str, object]]:
    if not LEDGER.exists():
        return {}
    ledger: dict[str, dict[str, object]] = json.loads(LEDGER.read_text(encoding="utf-8"))
    return ledger


def targets() -> list[Path]:
    return sorted(p for p in SPECS.glob("*.md") if p.name != "README.md")


def name_of(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def stale() -> list[str]:
    """台帳の sha256 と違うファイル。まだ書き込んでいないファイルも含む。"""
    ledger = load()
    return [
        name_of(path)
        for path in targets()
        if ledger.get(name_of(path), {}).get("sha256") != digest(path.read_text(encoding="utf-8"))
    ]


def status() -> int:
    names = stale()
    if not names:
        print(f"書き込みが要るファイルはありません（{len(targets())} 件とも台帳と一致）")
        return 0
    print(f"{len(names)} 件の仕様が、Confluence に反映されていません。")
    for name in names:
        print(f"  {name}")
    print("直し方: /sync-specs を実行してください。")
    return 1


def payload(path: Path) -> int:
    """MCPで書き込む本文。APIで書き込むページと同じ注意書きと sha256 を末尾に付ける。"""
    text = path.read_text(encoding="utf-8")
    source = name_of(path)
    print(text.rstrip("\n"))
    print()
    print(f"このページは {source} から自動で書き込まれます。直接編集しないでください。")
    print()
    print(f"docs-sync: {source} sha256:{digest(text)}")
    return 0


def record(path: Path, page_id: str, version: int) -> int:
    ledger = load()
    text = path.read_text(encoding="utf-8")
    ledger[name_of(path)] = {"sha256": digest(text), "page_id": page_id, "version": version}
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"記録しました  {name_of(path)} → ページ {page_id} v{version}")
    return 0


def check(path: Path, current_version: int) -> int:
    entry = load().get(name_of(path))
    if entry is None:
        print(f"{name_of(path)}: 台帳にありません。まだ書き込んでいないファイルです。")
        return 1
    if entry["sha256"] != digest(path.read_text(encoding="utf-8")):
        print(f"{name_of(path)}: ローカルが変わっています。書き込みが要ります。")
        return 1
    recorded = int(str(entry["version"]))
    if current_version == recorded:
        print(f"一致  {name_of(path)} v{recorded}（最後に書き込んだ版のまま。本文の取得は不要）")
        return 0
    print(f"{name_of(path)}: ページの版が v{recorded} から v{current_version} へ進んでいます。")
    print(
        "画面で編集されています。全文は取得せず、2つの版の差分だけを取得して中身を確かめてください。"
    )
    return 1


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["status"]:
        return status()
    if args[:1] == ["payload"] and len(args) == 2:
        return payload(Path(args[1]))
    if args[:1] == ["record"] and len(args) == 4:
        return record(Path(args[1]), args[2], int(args[3]))
    if args[:1] == ["check"] and len(args) == 3:
        return check(Path(args[1]), int(args[2]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
