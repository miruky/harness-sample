"""フックの記録を数える。どの柵が何回止めたかを見て、ハーネスのどこを直すかを決める。

uv run python tools/harness_stats.py            # .harness/logs/hooks.jsonl を数える
uv run python tools/harness_stats.py --log FILE # 別の記録を数える
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="フックの記録を数える")
    parser.add_argument("--log", type=Path, default=Path(".harness/logs/hooks.jsonl"))
    args = parser.parse_args(argv)
    entries = load(args.log)
    if not entries:
        print("記録がありません。")
        return 0
    sessions = {entry["session"] for entry in entries}
    by_hook: dict[str, Counter[str]] = {}
    reasons: Counter[str] = Counter()
    for entry in entries:
        by_hook.setdefault(entry["hook"], Counter())[entry["outcome"]] += 1
        if entry["outcome"] == "block":
            reasons[f"{entry['hook']}: {entry['detail'].splitlines()[0][:60]}"] += 1
    print(f"セッション {len(sessions)} 件、フックの実行 {len(entries)} 回\n")
    print(f"{'フック':<22}{'実行':>6}{'止めた':>6}{'諦めた':>6}")
    for hook, counts in sorted(by_hook.items()):
        total = sum(counts.values())
        print(f"{hook:<24}{total:>6}{counts['block']:>8}{counts['give_up']:>8}")
    if reasons:
        print("\n止めた理由（多い順）")
        for reason, count in reasons.most_common(10):
            print(f"{count:>4}  {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
