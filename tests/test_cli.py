from __future__ import annotations

import csv
import io
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


def test_list_date_and_room_show_only_matching_booking(capsys: pytest.CaptureFixture[str]) -> None:
    for room, start, end in (
        ("A", "2026-12-01T15:00+00:00", "2026-12-01T16:00+00:00"),
        ("B", "2026-12-02T10:00", "2026-12-02T11:00"),
        ("A", "2026-12-03T10:00", "2026-12-03T11:00"),
    ):
        assert run("add", "--room", room, "--owner", "miruky", "--start", start, "--end", end) == 0
    capsys.readouterr()
    assert run("list", "--date", "2026-12-02", "--room", "A") == 0
    output = capsys.readouterr()
    assert len(output.out.splitlines()) == 1
    assert "A  2026-12-02 00:00-01:00  miruky" in output.out
    assert output.err == ""


@pytest.mark.parametrize("day", ["2026-12-02", "2028-02-29"])
def test_list_date_without_matches_prints_nothing(
    day: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("list", "--date", day) == 0
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""


@pytest.mark.parametrize(
    "day", ["2026-02-29", "2026-13-01", "2026-12-1", "20261201", "2026-W49-2", "invalid", ""]
)
def test_list_invalid_date_exits_with_1_and_explains(
    day: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("list", "--date", day) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "日付は YYYY-MM-DD 形式の実在する日付で指定してください" in output.err


EXPORT_HEADER = "id,room,owner,start,end"


def export_lines(capsys: pytest.CaptureFixture[str], *options: str) -> list[str]:
    capsys.readouterr()
    assert run("export", "--format", "csv", *options) == 0
    output = capsys.readouterr()
    assert output.err == ""
    return output.out.splitlines()


def test_export_csv_prints_bookings_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    lines = export_lines(capsys)
    assert len(lines) == 2
    assert ",A,miruky," in lines[1]


def test_export_csv_first_line_is_header_in_column_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    assert export_lines(capsys)[0] == EXPORT_HEADER


def test_export_csv_writes_times_as_tokyo_iso8601(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "A", "2026-12-01T01:00+00:00", "2026-12-01T02:00+00:00")
    row = next(csv.reader(export_lines(capsys)[1:]))
    assert row[3:] == ["2026-12-01T10:00:00+09:00", "2026-12-01T11:00:00+09:00"]


def test_export_csv_is_sorted_by_start_then_room(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "B", "2026-12-01T10:00", "2026-12-01T11:00")
    book("miruky", "A", "2026-12-01T11:00", "2026-12-01T12:00")
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    rows = list(csv.reader(export_lines(capsys)[1:]))
    assert [(row[1], row[3]) for row in rows] == [
        ("A", "2026-12-01T10:00:00+09:00"),
        ("B", "2026-12-01T10:00:00+09:00"),
        ("A", "2026-12-01T11:00:00+09:00"),
    ]


def test_export_csv_room_option_keeps_only_that_room(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    book("aoi", "B", "2026-12-01T10:00", "2026-12-01T11:00")
    rows = list(csv.reader(export_lines(capsys, "--room", "B")[1:]))
    assert [(row[1], row[2]) for row in rows] == [("B", "aoi")]


def test_export_csv_without_bookings_prints_only_header(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert export_lines(capsys) == [EXPORT_HEADER]


def test_export_without_format_prints_same_as_csv(capsys: pytest.CaptureFixture[str]) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    expected = export_lines(capsys)
    assert run("export") == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert output.out.splitlines() == expected


@pytest.mark.parametrize("fmt", ["json", "CSV", "tsv", ""])
def test_export_unknown_format_exits_with_1_and_explains(
    fmt: str, capsys: pytest.CaptureFixture[str]
) -> None:
    book("miruky", "A", "2026-12-01T10:00", "2026-12-01T11:00")
    capsys.readouterr()
    assert run("export", "--format", fmt) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "csv を指定してください" in output.err


@pytest.mark.parametrize("owner", ["山田, 太郎", "改行\nあり", '引用符"あり', "両方,\r\n混在"])
def test_export_csv_keeps_columns_when_value_has_comma_or_newline(
    owner: str, capsys: pytest.CaptureFixture[str]
) -> None:
    book(owner, "A,B", "2026-12-01T10:00", "2026-12-01T11:00")
    capsys.readouterr()
    assert run("export", "--format", "csv") == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out)))
    assert rows[0] == EXPORT_HEADER.split(",")
    assert len(rows) == 2
    assert rows[1][1:3] == ["A,B", owner]
    assert len(rows[1]) == 5
