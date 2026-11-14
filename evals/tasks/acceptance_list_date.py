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


def seed() -> None:
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
    run(
        "add",
        "--room",
        "B",
        "--owner",
        "ren",
        "--start",
        "2026-12-02T10:00",
        "--end",
        "2026-12-02T11:00",
    )
    run(
        "add",
        "--room",
        "A",
        "--owner",
        "sora",
        "--start",
        "2026-12-02T13:00",
        "--end",
        "2026-12-02T14:00",
    )


def test_date_filter_shows_only_that_day(capsys: pytest.CaptureFixture[str]) -> None:
    seed()
    capsys.readouterr()
    assert run("list", "--date", "2026-12-02") == 0
    out = capsys.readouterr().out
    assert "ren" in out and "sora" in out and "aoi" not in out


def test_date_and_room_combine(capsys: pytest.CaptureFixture[str]) -> None:
    seed()
    capsys.readouterr()
    assert run("list", "--date", "2026-12-02", "--room", "A") == 0
    out = capsys.readouterr().out
    assert "sora" in out and "ren" not in out and "aoi" not in out


def test_list_without_date_still_shows_all(capsys: pytest.CaptureFixture[str]) -> None:
    seed()
    capsys.readouterr()
    assert run("list") == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 3
