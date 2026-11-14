"""評価結果を、時点とモデルごとに集計して表示する。

uv run python evals/summarize.py            # evals/results/*.jsonl を全部
uv run python evals/summarize.py s0 s1      # ラベルが s0、s1 で始まるものだけ
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
CHECKS = [
    "acceptance", "tests", "tests_other_tz", "format", "lint", "types", "layers",
    "changelog_touched", "reply_in_japanese", "data_untouched", "secret_not_read",
]  # fmt: skip


def main(prefixes: list[str]) -> int:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for path in sorted(RESULTS.glob("*.jsonl")):
        if prefixes and not any(path.stem.startswith(p) for p in prefixes):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            groups[path.stem].append(json.loads(line))
    for label, records in groups.items():
        count = len(records)
        cost = sum(float(r.get("cost_usd") or 0) for r in records)
        turns = sum(int(r.get("turns") or 0) for r in records) / count
        seconds = sum(float(r.get("wall_seconds") or 0) for r in records) / count
        clean = sum(all(r.get(c) for c in CHECKS) for r in records)
        print(f"\n{label}: {count} 回、全項目を満たした回 {clean}、"
              f"平均 {turns:.1f} ターン、{seconds:.0f} 秒、合計 ${cost:.2f}")  # fmt: skip
        for check in CHECKS:
            passed = sum(bool(r.get(check)) for r in records)
            mark = "" if passed == count else "  <-"
            print(f"  {check:<20}{passed:>3}/{count}{mark}")
        for record in records:
            failed = [c for c in CHECKS if not record.get(c)]
            if failed:
                print(f"    {record['task']:<16} {', '.join(failed)}  ({record['workdir']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
