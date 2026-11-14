"""service が外側の層に求める形。実装は storage と cli が持つ。"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from booking.domain.models import Booking


class Clock(Protocol):
    def now(self) -> datetime: ...


class BookingRepository(Protocol):
    def list(self) -> list[Booking]: ...

    def get(self, booking_id: str) -> Booking | None: ...

    def save(self, booking: Booking) -> None: ...

    def delete(self, booking_id: str) -> None: ...
