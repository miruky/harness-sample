"""JSONファイルへの保存。書き込みは一時ファイルを経由し、途中で止まっても元のファイルを壊さない。"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from booking.domain.models import Booking, TimeRange


def _encode(booking: Booking) -> dict[str, Any]:
    return {
        "id": booking.id,
        "room": booking.room,
        "owner": booking.owner,
        "start": booking.time.start.isoformat(),
        "end": booking.time.end.isoformat(),
        "title": booking.title,
    }


def _decode(raw: dict[str, Any]) -> Booking:
    time = TimeRange(datetime.fromisoformat(raw["start"]), datetime.fromisoformat(raw["end"]))
    return Booking(
        id=raw["id"], room=raw["room"], owner=raw["owner"], time=time, title=raw.get("title", "")
    )


class JsonFileRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, Booking]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {item["id"]: _decode(item) for item in raw["bookings"]}

    def _store(self, items: dict[str, Booking]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"bookings": [_encode(b) for b in items.values()]}
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".bookings-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(tmp, self._path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def list(self) -> list[Booking]:
        return list(self._load().values())

    def get(self, booking_id: str) -> Booking | None:
        return self._load().get(booking_id)

    def save(self, booking: Booking) -> None:
        items = self._load()
        items[booking.id] = booking
        self._store(items)

    def delete(self, booking_id: str) -> None:
        items = self._load()
        items.pop(booking_id, None)
        self._store(items)
