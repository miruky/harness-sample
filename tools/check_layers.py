"""層の向きと時計の使い方を検査する。

違反を見つけたら、どこが、なぜだめで、どう直すかを1件ずつ出力する。
人が読むためだけでなく、エージェントがこの出力を読んで自分で直せるように書いてある。

  uv run python tools/check_layers.py            # src/booking を検査する
  uv run python tools/check_layers.py --root DIR # 別の場所を検査する（テスト用）
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

PACKAGE = "booking"

# 左の層が import してよい層。内側から外側へ domain → service → storage / cli の順。
ALLOWED: dict[str, set[str]] = {
    "domain": {"domain"},
    "service": {"domain", "service"},
    "storage": {"domain", "service", "storage"},
    "cli": {"domain", "service", "storage", "cli"},
}

# 現在時刻を直接取り出す呼び出し。domain と service では使わない。
CLOCK_CALLS = {
    ("datetime", "now"),
    ("datetime", "utcnow"),
    ("datetime", "today"),
    ("date", "today"),
    ("time", "time"),
}
CLOCK_FREE_LAYERS = {"domain", "service"}

LAYER_FIX = (
    "直し方: 内側の層に必要な型を service/ports.py の Protocol として定義し、"
    "実物は cli.py で組み立てて引数で渡してください。"
    "向きの決まりは docs/architecture.md にあります。"
)
CLOCK_FIX = (
    "直し方: 現在時刻は引数で受け取ってください。service では self._clock.now() を使い、"
    "domain の関数には now: datetime を渡します。"
    "理由は docs/decisions/0002-inject-clock.md にあります。"
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    rule: str
    message: str
    fix: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}\n    {self.fix}"


def layer_of(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if len(parts) == 1:
        return "cli" if parts[0] == "cli.py" else None
    return parts[0] if parts[0] in ALLOWED else None


def imported_layer(module: str) -> str | None:
    parts = module.split(".")
    if parts[0] != PACKAGE or len(parts) < 2:
        return None
    return parts[1] if parts[1] in ALLOWED else None


def check_file(path: Path, root: Path) -> list[Violation]:
    layer = layer_of(path, root)
    if layer is None:
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[Violation] = []
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        elif isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        for module in modules:
            target = imported_layer(module)
            if target is not None and target not in ALLOWED[layer]:
                message = f"{layer} から {target} を import しています（{module}）"
                line = getattr(node, "lineno", 0)
                found.append(Violation(path, line, "layer", message, LAYER_FIX))
        if (
            layer in CLOCK_FREE_LAYERS
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and (node.func.value.id, node.func.attr) in CLOCK_CALLS
        ):
            call = f"{node.func.value.id}.{node.func.attr}()"
            found.append(
                Violation(
                    path, node.lineno, "clock", f"{layer} で {call} を呼んでいます", CLOCK_FIX
                )
            )
    return found


def check_tree(root: Path) -> list[Violation]:
    found: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        found.extend(check_file(path, root))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="層の向きと時計の使い方を検査する")
    parser.add_argument("--root", type=Path, default=Path("src") / PACKAGE)
    args = parser.parse_args(argv)
    violations = check_tree(args.root)
    for violation in violations:
        print(violation.render())
    if violations:
        print(f"\n{len(violations)} 件の違反があります。")
        return 1
    print("層の向きと時計の使い方: 違反なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
