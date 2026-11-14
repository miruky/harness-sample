"""予約で起きる失敗。CLI はこの型を見て終了コードとメッセージを決める。"""

from __future__ import annotations


class BookingError(Exception):
    """予約の決まりごとに反したときの基底クラス。"""


class InvalidTimeRange(BookingError):
    """終了が開始以前、またはタイムゾーンのない日時。"""


class SlotAlignmentError(BookingError):
    """開始か終了が15分単位になっていない。"""


class TooLongError(BookingError):
    """1件の予約が上限の長さを超えている。"""


class PastBookingError(BookingError):
    """開始が現在より前。"""


class OverlapError(BookingError):
    """同じ部屋の予約と時間が重なっている。"""

    def __init__(self, conflict_id: str) -> None:
        super().__init__(f"予約 {conflict_id} と時間が重なっています")
        self.conflict_id = conflict_id


class BookingNotFoundError(BookingError):
    """指定した予約が見つからない。"""
