import json
from enum import Enum
from typing import List


class SegmentType(Enum):
    UNKNOWN = "Unknown"
    COMMERCIAL = "Commercial"
    PREVIEW = "Preview"
    RECAP = "Recap"
    OUTRO = "Outro"
    INTRO = "Intro"


SUPPORTED_SEGMENT_TYPES = {
    SegmentType.INTRO,
    SegmentType.OUTRO,
    SegmentType.RECAP,
    SegmentType.PREVIEW,
    SegmentType.COMMERCIAL,
}


class MediaSegmentItem:
    def __init__(self, itemId: str, item_id: str, segment_type: SegmentType, start_ticks: int, end_ticks: int):
        self.itemId = itemId
        self.item_id = item_id
        self.segment_type = segment_type
        self.start_ticks = start_ticks
        self.end_ticks = end_ticks

    def get_segment_type_display(self):
        return self.segment_type.value

    def get_start_seconds(self):
        return self.ticks_to_seconds(self.start_ticks)

    def get_end_seconds(self):
        return self.ticks_to_seconds(self.end_ticks)

    @staticmethod
    def ticks_to_seconds(ticks: int) -> int:
        return ticks // 10000000

    @classmethod
    def from_dict(cls, data: dict):
        segment_type_value = data.get("Type", SegmentType.UNKNOWN.value)
        try:
            segment_type = SegmentType(segment_type_value)
        except ValueError:
            segment_type = SegmentType.UNKNOWN

        return cls(
            itemId=data.get("Id", ""),
            item_id=data.get("ItemId", ""),
            segment_type=segment_type,
            start_ticks=int(data.get("StartTicks", 0) or 0),
            end_ticks=int(data.get("EndTicks", 0) or 0)
        )

    def __str__(self):
        return f"{self.segment_type} - {self.start_ticks} - {self.end_ticks}"

    def __eq__(self, other):
        if not isinstance(other, MediaSegmentItem):
            return False

        same_item_id = other.item_id == self.item_id
        same_type = other.segment_type == self.segment_type
        same_start = other.get_start_seconds() == self.get_start_seconds()
        same_end = other.get_end_seconds() == self.get_end_seconds()

        return same_item_id and same_type and same_start and same_end


class MediaSegmentResponse:
    def __init__(self, items: List[MediaSegmentItem], total_record_count: int, start_index: int):
        self.items = items
        self.total_record_count = total_record_count
        self.start_index = start_index

    def get_next_item(self, current_seconds, only_upcoming=False, allowed_segment_types=None):
        """
        Get the next enabled item in the list based on the current time in seconds.
        If only_upcoming is True, it will only return upcoming items.
        If only_upcoming is False, it will return the first enabled item that is
        currently playing or the next enabled upcoming item.
        """
        allowed_segment_types = (
            {str(segment_type).lower() for segment_type in allowed_segment_types}
            if allowed_segment_types is not None
            else None
        )

        smallest_difference = None
        item_to_return = None
        for item in self.items:
            segment_type = item.get_segment_type_display().lower()
            if allowed_segment_types is not None and segment_type not in allowed_segment_types:
                continue

            start_seconds = item.get_start_seconds()
            end_seconds = item.get_end_seconds()

            if start_seconds <= current_seconds <= end_seconds and not only_upcoming:
                return item

            if start_seconds > current_seconds:
                difference = start_seconds - current_seconds
                if smallest_difference is None or difference < smallest_difference:
                    smallest_difference = difference
                    item_to_return = item

        return item_to_return

    @classmethod
    def from_json(cls, json_dict: dict, expected_item_id=None):
        data = json_dict or {}
        items = []

        for item_data in data.get("Items", []):
            try:
                item = MediaSegmentItem.from_dict(item_data)
            except (TypeError, ValueError):
                continue

            if item.segment_type not in SUPPORTED_SEGMENT_TYPES:
                continue

            if expected_item_id is not None and str(item.item_id) != str(expected_item_id):
                continue

            if item.end_ticks <= item.start_ticks:
                continue

            items.append(item)

        return cls(
            items=items,
            total_record_count=len(items),
            start_index=int(data.get("StartIndex", 0) or 0)
        )

    def get_items_by_type(self, segment_type: SegmentType) -> List[MediaSegmentItem]:
        return [item for item in self.items if item.segment_type == segment_type]

    def __str__(self):
        json_dict = {
            "Items": [str(item) for item in self.items],
            "TotalRecordCount": self.total_record_count,
            "StartIndex": self.start_index
        }
        return json.dumps(json_dict)
