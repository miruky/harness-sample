from __future__ import annotations

from datetime import datetime

import pytest

from booking.domain.errors import InvalidTimeRange
from booking.domain.models import TimeRange
from tests.conftest import at


def test_adjacent_ranges_do_not_overlap() -> None:
    assert not TimeRange(at(10), at(11)).overlaps(TimeRange(at(11), at(12)))


def test_partial_overlap_is_detected_in_both_directions() -> None:
    first, second = TimeRange(at(10), at(11)), TimeRange(at(10, 30), at(11, 30))
    assert first.overlaps(second)
    assert second.overlaps(first)


def test_end_must_be_after_start() -> None:
    with pytest.raises(InvalidTimeRange):
        TimeRange(at(11), at(11))


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(InvalidTimeRange):
        TimeRange(datetime(2026, 12, 1, 10), datetime(2026, 12, 1, 11))
