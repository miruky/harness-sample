"""予約を受け付ける条件。現在時刻は引数で受け取り、ここでは時計を見ない。"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from booking.domain.errors import (
    OverlapError,
    PastBookingError,
    SlotAlignmentError,
    TooLongError,
)
from booking.domain.models import Booking, TimeRange

SLOT_MINUTES = 15
MAX_DURATION = timedelta(hours=4)


def _on_slot(moment: datetime) -> bool:
    return moment.minute % SLOT_MINUTES == 0 and moment.second == 0 and moment.microsecond == 0


def validate_new_booking(
    candidate: TimeRange, room: str, existing: Iterable[Booking], now: datetime
) -> None:
    """受け付けられない予約なら BookingError の派生を送出する。"""
    if not (_on_slot(candidate.start) and _on_slot(candidate.end)):
        raise SlotAlignmentError(f"開始と終了は{SLOT_MINUTES}分単位にしてください")
    if candidate.duration > MAX_DURATION:
        raise TooLongError("1件の予約は4時間までです")
    if candidate.start < now:
        raise PastBookingError("過去の時刻は予約できません")
    for booking in existing:
        if booking.room == room and booking.time.overlaps(candidate):
            raise OverlapError(booking.id)
