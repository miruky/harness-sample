from __future__ import annotations

from datetime import UTC, timedelta

import pytest

from booking.domain.errors import (
    BookingNotFoundError,
    OverlapError,
    PastBookingError,
    SlotAlignmentError,
    TooLongError,
)
from booking.service.booking_service import BookingService
from tests.conftest import FixedClock, at


def test_create_returns_saved_booking(service: BookingService) -> None:
    booking = service.create("A", "miruky", at(10), at(11), "定例")
    assert booking.id == "b001"
    assert service.list() == [booking]


def test_same_room_overlap_is_rejected(service: BookingService) -> None:
    service.create("A", "miruky", at(10), at(11))
    with pytest.raises(OverlapError) as caught:
        service.create("A", "guest", at(10, 30), at(11, 30))
    assert caught.value.conflict_id == "b001"


def test_other_room_can_share_the_same_time(service: BookingService) -> None:
    service.create("A", "miruky", at(10), at(11))
    assert service.create("B", "guest", at(10), at(11)).room == "B"


def test_back_to_back_bookings_are_accepted(service: BookingService) -> None:
    service.create("A", "miruky", at(10), at(11))
    assert service.create("A", "guest", at(11), at(12)).id == "b002"


def test_start_must_be_on_a_15_minute_slot(service: BookingService) -> None:
    with pytest.raises(SlotAlignmentError):
        service.create("A", "miruky", at(10, 10), at(11))


def test_longer_than_four_hours_is_rejected(service: BookingService) -> None:
    with pytest.raises(TooLongError):
        service.create("A", "miruky", at(9), at(13, 15))


def test_exactly_four_hours_is_accepted(service: BookingService) -> None:
    booking = service.create("A", "miruky", at(9), at(13))
    assert booking.time.duration == timedelta(hours=4)


def test_past_start_is_rejected(service: BookingService) -> None:
    with pytest.raises(PastBookingError):
        service.create("A", "miruky", at(7), at(8))


def test_start_exactly_now_is_accepted(service: BookingService) -> None:
    assert service.create("A", "miruky", at(8), at(9)).time.start == at(8)


def test_cancel_frees_the_slot(service: BookingService) -> None:
    booking = service.create("A", "miruky", at(10), at(11))
    service.cancel(booking.id)
    assert service.list() == []
    assert service.create("A", "guest", at(10), at(11)).owner == "guest"


def test_cancel_unknown_id_fails(service: BookingService) -> None:
    with pytest.raises(BookingNotFoundError):
        service.cancel("nope")


def test_list_is_sorted_by_start_and_filtered_by_room(service: BookingService) -> None:
    late = service.create("A", "miruky", at(15), at(16))
    early = service.create("A", "miruky", at(9), at(10))
    service.create("B", "guest", at(9), at(10))
    assert service.list("A") == [early, late]


def test_totals_are_summed_per_owner(service: BookingService) -> None:
    service.create("A", "miruky", at(10), at(11))
    service.create("B", "miruky", at(13), at(15, 30))
    [total] = service.totals_by_owner()
    assert (total.owner, total.total) == ("miruky", timedelta(hours=3.5))


def test_totals_are_sorted_by_hours_desc_then_owner(service: BookingService) -> None:
    service.create("A", "ren", at(10), at(11))
    service.create("B", "aoi", at(10), at(11))
    service.create("C", "sora", at(10), at(12))
    assert [t.owner for t in service.totals_by_owner()] == ["sora", "aoi", "ren"]


def test_started_bookings_are_not_counted(service: BookingService, clock: FixedClock) -> None:
    service.create("A", "aoi", at(10), at(12))
    service.create("A", "ren", at(13), at(14))
    clock.moment = at(11)
    assert [t.owner for t in service.totals_by_owner()] == ["ren"]


def test_booking_starting_now_is_counted(service: BookingService, clock: FixedClock) -> None:
    service.create("A", "aoi", at(10), at(11))
    clock.moment = at(10)
    assert [t.owner for t in service.totals_by_owner()] == ["aoi"]


def test_no_upcoming_bookings_gives_empty_totals(service: BookingService) -> None:
    assert service.totals_by_owner() == []


def test_list_date_uses_tokyo_start_day_and_midnight_boundaries(service: BookingService) -> None:
    service.create("A", "miruky", at(23, 45), at(0, 15, day=2))
    last = service.create("A", "miruky", at(23, 45, day=2), at(0, 15, day=3))
    first = service.create("B", "guest", at(0, day=2).astimezone(UTC), at(1, day=2).astimezone(UTC))
    service.create("B", "guest", at(0, day=3).astimezone(UTC), at(1, day=3).astimezone(UTC))
    assert service.list(on_date=at(0, day=2).date()) == [first, last]


def test_list_date_and_room_filters_are_combined_and_sorted(service: BookingService) -> None:
    late = service.create("A", "miruky", at(15), at(16))
    early = service.create("A", "miruky", at(9), at(10))
    service.create("B", "guest", at(9), at(10))
    service.create("A", "miruky", at(9, day=2), at(10, day=2))
    assert service.list("A", on_date=at(0).date()) == [early, late]


def test_list_without_date_includes_all_days(service: BookingService) -> None:
    later = service.create("A", "miruky", at(9, day=2), at(10, day=2))
    earlier = service.create("A", "miruky", at(9), at(10))
    assert service.list() == [earlier, later]


def test_list_date_without_matches_returns_empty(service: BookingService) -> None:
    service.create("A", "miruky", at(9), at(10))
    assert service.list(on_date=at(0, day=2).date()) == []


def test_list_date_includes_past_bookings(service: BookingService, clock: FixedClock) -> None:
    booking = service.create("A", "miruky", at(9), at(10))
    clock.moment = at(8, day=3)
    assert service.list(on_date=at(0).date()) == [booking]
