from __future__ import annotations

from pathlib import Path

import pytest

from booking.cli import main
from tests.conftest import FixedClock, at


@pytest.fixture(autouse=True)
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKING_DB", str(tmp_path / "bookings.json"))


def run(*argv: str) -> int:
    return main(list(argv), clock=FixedClock(at(8)))


def test_add_then_list(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        run(
            "add",
            "--room",
            "A",
            "--owner",
            "miruky",
            "--start",
            "2026-12-01T10:00",
            "--end",
            "2026-12-01T11:00",
        )
        == 0
    )
    capsys.readouterr()
    assert run("list") == 0
    assert "A  2026-12-01 10:00-11:00  miruky" in capsys.readouterr().out


def test_overlap_exits_with_1_and_explains(capsys: pytest.CaptureFixture[str]) -> None:
    common = ("--room", "A", "--owner", "miruky")
    run("add", *common, "--start", "2026-12-01T10:00", "--end", "2026-12-01T11:00")
    assert run("add", *common, "--start", "2026-12-01T10:30", "--end", "2026-12-01T11:30") == 1
    assert "時間が重なっています" in capsys.readouterr().err


def test_cancel_unknown_booking_exits_with_1() -> None:
    assert run("cancel", "nope") == 1


def book(owner: str, room: str, start: str, end: str) -> None:
    assert run("add", "--room", room, "--owner", owner, "--start", start, "--end", end) == 0


def test_stats_prints_owner_and_hours(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    book("miruky", "B", "2026-12-01T13:00", "2026-12-01T15:45")
    book("aoi", "A", "2026-12-02T10:00", "2026-12-02T11:00")
    capsys.readouterr()
    assert run("stats") == 0
    assert capsys.readouterr().out.splitlines() == ["miruky 3.75h", "aoi 1.0h"]
