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
        return cls(
            itemId=data["Id"],
            item_id=data["ItemId"],
            segment_type=SegmentType(data["Type"]),
            start_ticks=data["StartTicks"],
            end_ticks=data["EndTicks"]
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

    def get_next_item(self, current_seconds, only_upcoming=False):
        """
        Get the next item in the list based on the current time in seconds.
        If only_upcoming is True, it will only return upcoming items.
        If only_upcoming is False, it will return the first item that is currently playing or the next upcoming item.
        E.g. if the current time is 10 seconds and the next item starts at 20 seconds, it will return that item.
        If the current time is 10 seconds and an item starts at 5 seconds and ends at 15 seconds, it will return that item only if only_upcoming is false.

        :param current_seconds: The current time in seconds.
        :param only_upcoming: If True, only return upcoming items. If False, return the first item that is currently playing or the next upcoming item.
        :return: The next item in the list based on the current time in seconds.
        """
        smallest_difference = None
        item_to_return = None
        for item in self.items:
            start_seconds = item.get_start_seconds()
            end_seconds = item.get_end_seconds()

            if start_seconds < current_seconds < end_seconds and not only_upcoming:
                return item

            if start_seconds > current_seconds:
                if not smallest_difference or start_seconds - current_seconds < smallest_difference:
                    smallest_difference = start_seconds - current_seconds
                    item_to_return = item

        return item_to_return

    @classmethod
    def from_json(cls, json_dict: dict):
        data = json_dict
        items = [MediaSegmentItem.from_dict(item) for item in data["Items"]]
        return cls(
            items=items,
            total_record_count=data["TotalRecordCount"],
            start_index=data["StartIndex"]
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