from __future__ import annotations

from pathlib import Path

import pytest

from booking.cli import main
from tests.conftest import FixedClock, at


@pytest.fixture(autouse=True)
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKING_DB", str(tmp_path / "bookings.json"))


def add(start: str, end: str) -> int:
    # 2026-11-30 は月曜。時計は月曜の朝6時に固定する
    clock = FixedClock(at(6).replace(month=11, day=30))
    return main(
        ["add", "--room", "A", "--owner", "aoi", "--start", start, "--end", end], clock=clock
    )


def test_weekday_inside_hours_is_accepted() -> None:
    assert add("2026-12-01T09:00", "2026-12-01T10:00") == 0
    assert add("2026-12-01T17:00", "2026-12-01T18:00") == 0


def test_before_opening_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    assert add("2026-12-01T08:45", "2026-12-01T09:45") == 1
    assert capsys.readouterr().err.strip() != ""


def test_past_closing_is_refused() -> None:
    assert add("2026-12-01T17:30", "2026-12-01T18:30") == 1


def test_weekend_is_refused() -> None:
    assert add("2026-12-05T10:00", "2026-12-05T11:00") == 1
    assert add("2026-12-06T10:00", "2026-12-06T11:00") == 1


def test_hours_are_judged_in_tokyo_time() -> None:
    # UTC の 00:00 は東京の 09:00
    assert add("2026-12-01T00:00+00:00", "2026-12-01T01:00+00:00") == 0
    # UTC の 10:00 は東京の 19:00
    assert add("2026-12-01T10:00+00:00", "2026-12-01T11:00+00:00") == 1
