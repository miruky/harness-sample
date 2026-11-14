from __future__ import annotations

from pathlib import Path

import pytest

from booking.cli import main
from tests.conftest import FixedClock, at


@pytest.fixture(autouse=True)
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKING_DB", str(tmp_path / "bookings.json"))


def add(owner: str, room: str, start: str, end: str) -> None:
    assert (
        main(
            ["add", "--room", room, "--owner", owner, "--start", start, "--end", end],
            clock=FixedClock(at(8)),
        )
        == 0
    )


def test_totals_are_sorted_by_hours_then_name(capsys: pytest.CaptureFixture[str]) -> None:
    add("ren", "A", "2026-12-01T10:00", "2026-12-01T11:30")
    add("aoi", "B", "2026-12-01T10:00", "2026-12-01T12:00")
    add("aoi", "A", "2026-12-02T10:00", "2026-12-02T11:30")
    add("sora", "B", "2026-12-02T10:00", "2026-12-02T11:30")
    capsys.readouterr()
    assert main(["stats"], clock=FixedClock(at(8))) == 0
    assert capsys.readouterr().out.strip().splitlines() == ["aoi 3.5h", "ren 1.5h", "sora 1.5h"]


def test_only_upcoming_bookings_are_counted(capsys: pytest.CaptureFixture[str]) -> None:
    add("aoi", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    add("ren", "A", "2026-12-03T10:00", "2026-12-03T11:00")
    capsys.readouterr()
    # 時計を12月2日へ進めると、12月1日の予約は対象から外れる
    assert main(["stats"], clock=FixedClock(at(8, day=2))) == 0
    assert capsys.readouterr().out.strip().splitlines() == ["ren 1.0h"]


def test_no_bookings_prints_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats"], clock=FixedClock(at(8))) == 0
    assert capsys.readouterr().out.strip() == ""
