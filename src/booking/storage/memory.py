"""メモリ上の保存先。テストで使う。"""

from __future__ import annotations

from booking.domain.models import Booking


class InMemoryRepository:
    def __init__(self) -> None:
        self._items: dict[str, Booking] = {}

    def list(self) -> list[Booking]:
        return list(self._items.values())

    def get(self, booking_id: str) -> Booking | None:
        return self._items.get(booking_id)

    def save(self, booking: Booking) -> None:
        self._items[booking.id] = booking

    def delete(self, booking_id: str) -> None:
        self._items.pop(booking_id, None)
