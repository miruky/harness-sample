"""予約の作成、取り消し、一覧、集計。"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from booking.domain.errors import BookingNotFoundError
from booking.domain.models import Booking, OwnerTotal, TimeRange
from booking.domain.rules import validate_new_booking
from booking.service.ports import BookingRepository, Clock

TOKYO = ZoneInfo("Asia/Tokyo")


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class BookingService:
    def __init__(
        self,
        repository: BookingRepository,
        clock: Clock,
        id_factory: Callable[[], str] = _new_id,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_factory = id_factory

    def create(
        self, room: str, owner: str, start: datetime, end: datetime, title: str = ""
    ) -> Booking:
        time = TimeRange(start, end)
        validate_new_booking(time, room, self._repository.list(), self._clock.now())
        booking = Booking(id=self._id_factory(), room=room, owner=owner, time=time, title=title)
        self._repository.save(booking)
        return booking

    def cancel(self, booking_id: str) -> None:
        if self._repository.get(booking_id) is None:
            raise BookingNotFoundError(f"予約 {booking_id} は見つかりません")
        self._repository.delete(booking_id)

    def totals_by_owner(self) -> list[OwnerTotal]:
        """これから始まる予約（開始が現在以降）の長さを予約者ごとに合計する。

        多い順に並べ、同じ長さなら予約者の名前順にする。
        """
        now = self._clock.now()
        totals: dict[str, timedelta] = {}
        for booking in self._repository.list():
            if booking.time.start >= now:
                totals[booking.owner] = (
                    totals.get(booking.owner, timedelta()) + booking.time.duration
                )
        ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
        return [OwnerTotal(owner, total) for owner, total in ranked]

    def list(self, room: str | None = None, on_date: date | None = None) -> list[Booking]:
        bookings = self._repository.list()
        if room is not None:
            bookings = [b for b in bookings if b.room == room]
        if on_date is not None:
            bookings = [b for b in bookings if b.time.start.astimezone(TOKYO).date() == on_date]
        return sorted(bookings, key=lambda b: (b.time.start, b.room))
