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


def lines(capsys: pytest.CaptureFixture[str]) -> list[str]:
    return capsys.readouterr().out.strip().splitlines()


def test_three_weeks_create_three_bookings(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        run(
            "add",
            "--room",
            "A",
            "--owner",
            "aoi",
            "--start",
            "2026-12-01T10:00",
            "--end",
            "2026-12-01T11:00",
            "--repeat-weekly",
            "3",
        )
        == 0
    )
    assert len(lines(capsys)) == 3
    assert run("list") == 0
    out = "\n".join(lines(capsys))
    assert "2026-12-01 10:00-11:00" in out
    assert "2026-12-08 10:00-11:00" in out
    assert "2026-12-15 10:00-11:00" in out


def test_one_conflict_creates_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        run(
            "add",
            "--room",
            "A",
            "--owner",
            "ren",
            "--start",
            "2026-12-15T10:30",
            "--end",
            "2026-12-15T11:30",
        )
        == 0
    )
    capsys.readouterr()
    assert (
        run(
            "add",
            "--room",
            "A",
            "--owner",
            "aoi",
            "--start",
            "2026-12-01T10:00",
            "--end",
            "2026-12-01T11:00",
            "--repeat-weekly",
            "3",
        )
        == 1
    )
    capsys.readouterr()
    assert run("list") == 0
    listed = lines(capsys)
    assert len(listed) == 1 and "ren" in listed[0]


def test_without_the_option_one_booking_is_created(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        run(
            "add",
            "--room",
            "A",
            "--owner",
            "aoi",
            "--start",
            "2026-12-01T10:00",
            "--end",
            "2026-12-01T11:00",
        )
        == 0
    )
    assert len(lines(capsys)) == 1
