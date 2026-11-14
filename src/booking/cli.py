"""コマンドラインの入口。時計と保存先の実物を組み立てて service へ渡す。"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from booking.domain.errors import BookingError
from booking.domain.models import Booking, OwnerTotal
from booking.service.booking_service import BookingService
from booking.service.ports import Clock
from booking.storage.json_file import JsonFileRepository

TOKYO = ZoneInfo("Asia/Tokyo")
EXIT_OK = 0
EXIT_REJECTED = 1
EXPORT_FORMATS = ("csv",)
CSV_COLUMNS = ("id", "room", "owner", "start", "end")


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(TOKYO)


def _parse_moment(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=TOKYO)


def _parse_date(text: str) -> date:
    try:
        parsed = date.fromisoformat(text)
        if parsed.isoformat() != text:
            raise ValueError
    except ValueError as error:
        raise BookingError("日付は YYYY-MM-DD 形式の実在する日付で指定してください") from error
    return parsed


def _format(booking: Booking) -> str:
    start = booking.time.start.astimezone(TOKYO)
    end = booking.time.end.astimezone(TOKYO)
    line = f"{booking.id}  {booking.room}  {start:%Y-%m-%d %H:%M}-{end:%H:%M}  {booking.owner}"
    return f"{line}  {booking.title}" if booking.title else line


def _format_total(total: OwnerTotal) -> str:
    # 15分単位なので小数第2位まであれば正確に出せる。末尾の0は1桁まで削る（3.50 → 3.5、1.00 → 1.0）
    hours = f"{total.total.total_seconds() / 3600:.2f}".rstrip("0")
    if hours.endswith("."):
        hours += "0"
    return f"{total.owner} {hours}h"


def _write_csv(bookings: Sequence[Booking]) -> None:
    # カンマ、引用符、改行を含む値は csv モジュールが引用符で囲むので、列がずれない
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for booking in bookings:
        writer.writerow(
            (
                booking.id,
                booking.room,
                booking.owner,
                booking.time.start.astimezone(TOKYO).isoformat(timespec="seconds"),
                booking.time.end.astimezone(TOKYO).isoformat(timespec="seconds"),
            )
        )


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
    listing.add_argument("--date", metavar="YYYY-MM-DD", help="東京時間で指定日に始まる予約")

    cancel = sub.add_parser("cancel", help="予約を取り消す")
    cancel.add_argument("booking_id")

    sub.add_parser("stats", help="これから始まる予約の合計時間を予約者ごとに出す")

    export = sub.add_parser("export", help="予約を標準出力へ書き出す")
    export.add_argument(
        "--format", default="csv", help="出力の形式。いまは csv だけ（省略すると csv）"
    )
    export.add_argument("--room")
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
            on_date = _parse_date(args.date) if args.date is not None else None
            for booking in service.list(args.room, on_date=on_date):
                print(_format(booking))
        elif args.command == "cancel":
            service.cancel(args.booking_id)
            print(f"取り消しました: {args.booking_id}")
        elif args.command == "stats":
            for total in service.totals_by_owner():
                print(_format_total(total))
        elif args.command == "export":
            if args.format not in EXPORT_FORMATS:
                raise BookingError(
                    f"形式 {args.format} には対応していません。csv を指定してください"
                )
            _write_csv(service.list(args.room))
    except BookingError as error:
        print(f"受け付けられません: {error}", file=sys.stderr)
        return EXIT_REJECTED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
