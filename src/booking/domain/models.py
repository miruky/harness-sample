"""予約と時間帯のデータ。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from booking.domain.errors import InvalidTimeRange


@dataclass(frozen=True)
class TimeRange:
    """開始を含み、終了を含まない時間帯。10:00-11:00 と 11:00-12:00 は重ならない。"""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise InvalidTimeRange("日時にはタイムゾーンが必要です")
        if self.end <= self.start:
            raise InvalidTimeRange("終了は開始より後にしてください")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps(self, other: TimeRange) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Booking:
    id: str
    room: str
    owner: str
    time: TimeRange
    title: str = ""
