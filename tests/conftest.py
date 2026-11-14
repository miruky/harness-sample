from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from booking.service.booking_service import BookingService
from booking.storage.memory import InMemoryRepository

TOKYO = ZoneInfo("Asia/Tokyo")


class FixedClock:
    """テスト用の時計。いつ実行しても同じ時刻を返す。"""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


def at(hour: int, minute: int = 0, day: int = 1) -> datetime:
    """2026年12月の指定した日時（東京）。"""
    return datetime(2026, 12, day, hour, minute, tzinfo=TOKYO)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(at(8))


@pytest.fixture
def service(clock: FixedClock) -> BookingService:
    ids = iter(f"b{n:03d}" for n in range(1, 1000))
    return BookingService(InMemoryRepository(), clock, id_factory=lambda: next(ids))
