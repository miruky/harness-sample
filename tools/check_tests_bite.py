"""テストが、決まりの書き換えに気づくかを確かめる。

  uv run python tools/check_tests_bite.py

予約の決まりを1か所ずつわざと書き換え、そのたびにテストを走らせる。
テストが落ちれば、その決まりは見張られている。通ってしまえば、見張るテストがない。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# (ファイル, 元の書き方, 書き換えた書き方, 何を変えたか)
CHANGES: list[tuple[str, str, str, str]] = [
    ("src/booking/domain/rules.py", "timedelta(hours=4)", "timedelta(hours=3)",
     "最長を4時間から3時間に"),
    ("src/booking/domain/rules.py", "timedelta(hours=4)", "timedelta(hours=5)",
     "最長を4時間から5時間に"),
    ("src/booking/domain/rules.py", "candidate.duration > MAX_DURATION",
     "candidate.duration >= MAX_DURATION", "ちょうど4時間も断る"),
    ("src/booking/domain/rules.py", "SLOT_MINUTES = 15", "SLOT_MINUTES = 5",
     "15分単位を5分単位に"),
    ("src/booking/domain/rules.py", "candidate.start < now", "candidate.start <= now",
     "いまちょうどに始まる予約も断る"),
    ("src/booking/domain/rules.py", "booking.room == room and", "", "別の部屋との重なりも断る"),
]  # fmt: skip


def tests_fail() -> bool:
    done = subprocess.run(
        ["uv", "run", "pytest", "-x", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True,
    )  # fmt: skip
    return done.returncode != 0


def main() -> int:
    missed = 0
    for name, old, new, what in CHANGES:
        path = ROOT / name
        original = path.read_text(encoding="utf-8")
        if old not in original:
            print(f"書き換え先が見つかりません: {name} の {old}")
            return 2
        try:
            path.write_text(original.replace(old, new, 1), encoding="utf-8")
            caught = tests_fail()
        finally:
            path.write_text(original, encoding="utf-8")
        print(f"{'気づいた  ' if caught else '見逃した  '}{what}")
        missed += not caught
    if missed:
        print(f"\n{missed} 件の書き換えを、テストが見逃しました。")
        print("直し方: 見逃した決まりの、ちょうどの値と1つ外の値を確かめるテストを足してください。")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
