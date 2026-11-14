from __future__ import annotations

from pathlib import Path

from tools.check_layers import check_tree


def write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def test_the_real_package_has_no_violation() -> None:
    assert check_tree(Path("src/booking")) == []


def test_domain_importing_storage_is_reported_with_a_fix(tmp_path: Path) -> None:
    write(tmp_path, "domain/rules.py", "from booking.storage.memory import InMemoryRepository\n")
    (violation,) = check_tree(tmp_path)
    assert violation.rule == "layer"
    assert "直し方" in violation.fix


def test_clock_call_in_service_is_reported(tmp_path: Path) -> None:
    write(tmp_path, "service/x.py", "from datetime import datetime\nnow = datetime.now()\n")
    (violation,) = check_tree(tmp_path)
    assert violation.rule == "clock"
    assert violation.line == 2


def test_clock_call_in_cli_is_allowed(tmp_path: Path) -> None:
    write(tmp_path, "cli.py", "from datetime import datetime\nnow = datetime.now()\n")
    assert check_tree(tmp_path) == []
