from __future__ import annotations

from pathlib import Path

import pytest

from booking.cli import main
from tests.conftest import FixedClock, at


@pytest.fixture(autouse=True)
def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKING_DB", str(tmp_path / "bookings.json"))


def add(capsys: pytest.CaptureFixture[str], start: str, end: str) -> str:
    assert (
        main(
            ["add", "--room", "A", "--owner", "aoi", "--start", start, "--end", end],
            clock=FixedClock(at(8)),
        )
        == 0
    )
    return capsys.readouterr().out.split()[0]


def test_cancel_within_an_hour_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    booking_id = add(capsys, "2026-12-01T10:00", "2026-12-01T11:00")
    assert main(["cancel", booking_id], clock=FixedClock(at(9, 30))) == 1
    assert capsys.readouterr().err.strip() != ""
    assert main(["list"], clock=FixedClock(at(9, 30))) == 0
    assert booking_id in capsys.readouterr().out


def test_cancel_exactly_one_hour_before_is_allowed(capsys: pytest.CaptureFixture[str]) -> None:
    booking_id = add(capsys, "2026-12-01T10:00", "2026-12-01T11:00")
    assert main(["cancel", booking_id], clock=FixedClock(at(9))) == 0


def test_cancel_after_start_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    booking_id = add(capsys, "2026-12-01T10:00", "2026-12-01T11:00")
    assert main(["cancel", booking_id], clock=FixedClock(at(10, 15))) == 1
