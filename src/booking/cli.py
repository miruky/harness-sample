"""コマンドラインの入口。時計と保存先の実物を組み立てて service へ渡す。"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from booking.domain.errors import BookingError
from booking.domain.models import Booking
from booking.service.booking_service import BookingService
from booking.service.ports import Clock
from booking.storage.json_file import JsonFileRepository

TOKYO = ZoneInfo("Asia/Tokyo")
EXIT_OK = 0
EXIT_REJECTED = 1


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(TOKYO)


def _parse_moment(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=TOKYO)


def _format(booking: Booking) -> str:
    start = booking.time.start.astimezone(TOKYO)
    end = booking.time.end.astimezone(TOKYO)
    line = f"{booking.id}  {booking.room}  {start:%Y-%m-%d %H:%M}-{end:%H:%M}  {booking.owner}"
    return f"{line}  {booking.title}" if booking.title else line


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="booking", description="会議室を予約する")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="予約を作る")
    add.add_argument("--room", required=True)
    add.add_argument("--owner", required=True)
    add.add_argument("--start", required=True, type=_parse_moment, help="例 2026-12-01T10:00")
    add.add_argument("--end", required=True, type=_parse_moment, help="例 2026-12-01T11:00")
    add.add_argument("--title", default="")

    listing = sub.add_parser("list", help="予約を一覧する")
    listing.add_argument("--room")

    cancel = sub.add_parser("cancel", help="予約を取り消す")
    cancel.add_argument("booking_id")
    return parser


def main(argv: Sequence[str] | None = None, clock: Clock | None = None) -> int:
    args = _build_parser().parse_args(argv)
    path = Path(os.environ.get("BOOKING_DB", "bookings.json"))
    service = BookingService(JsonFileRepository(path), clock or SystemClock())
    try:
        if args.command == "add":
            booking = service.create(args.room, args.owner, args.start, args.end, args.title)
            print(_format(booking))
        elif args.command == "list":
            for booking in service.list(args.room):
                print(_format(booking))
        elif args.command == "cancel":
            service.cancel(args.booking_id)
            print(f"取り消しました: {args.booking_id}")
    except BookingError as error:
        print(f"受け付けられません: {error}", file=sys.stderr)
        return EXIT_REJECTED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
