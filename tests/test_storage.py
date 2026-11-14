from __future__ import annotations

from pathlib import Path

from booking.domain.models import Booking, TimeRange
from booking.storage.json_file import JsonFileRepository
from tests.conftest import at


def test_saved_booking_survives_a_new_repository(tmp_path: Path) -> None:
    path = tmp_path / "db" / "bookings.json"
    booking = Booking("b001", "A", "miruky", TimeRange(at(10), at(11)), "定例")
    JsonFileRepository(path).save(booking)
    assert JsonFileRepository(path).list() == [booking]


def test_delete_removes_only_the_target(tmp_path: Path) -> None:
    repository = JsonFileRepository(tmp_path / "bookings.json")
    keep = Booking("b001", "A", "miruky", TimeRange(at(10), at(11)))
    drop = Booking("b002", "A", "miruky", TimeRange(at(11), at(12)))
    repository.save(keep)
    repository.save(drop)
    repository.delete("b002")
    assert repository.list() == [keep]
    assert repository.get("b002") is None


def test_no_temporary_file_is_left_behind(tmp_path: Path) -> None:
    repository = JsonFileRepository(tmp_path / "bookings.json")
    repository.save(Booking("b001", "A", "miruky", TimeRange(at(10), at(11))))
    assert [p.name for p in tmp_path.iterdir()] == ["bookings.json"]
