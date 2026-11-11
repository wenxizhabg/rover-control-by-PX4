"""US-04/T4: terminal và đồng hồ giả lập dùng trong test."""

from rover.screen import ViewModel, render
from rover.types import VehicleEvent


class FakeClock:
    """Đồng hồ giả lập có thể tăng thời gian theo yêu cầu."""

    def __init__ (self, start: float = 0.0) -> None:
        self ._time = start

    def now (self) -> float:
        """Trả thời gian giả lập hiện tại."""
        return self ._time

    def advance (self, seconds: float) -> None:
        """Tăng thời gian giả lập."""
        self ._time += seconds


class FakeTerminal:
    """Terminal giả lập đọc lần lượt phím và lưu khung cuối được vẽ."""

    def __init__ (self, keys: list[str] | None = None) -> None:
        self ._keys = list (keys or [])
        self .last_lines: list[str] = []
        self .closed = False

    def read_key (self) -> str | None:
        """Trả phím kế tiếp hoặc None khi danh sách đã hết."""
        if not self ._keys:
            return None
        return self ._keys .pop (0)

    def draw (self, lines: list[str]) -> None:
        """Lưu khung cuối cùng được yêu cầu hiển thị."""
        self .last_lines = list (lines)

    def close (self) -> None:
        """Đánh dấu terminal giả lập đã được đóng."""
        self .closed = True


class FakeVehicleLink:
    """Kênh xe giả lập, trả các sự kiện đã xếp sẵn cho lần poll kế tiếp."""

    def __init__ (self) -> None:
        self ._events: list[VehicleEvent] = []
        self .closed = False

    def push (self, event: VehicleEvent) -> None:
        """Xếp một sự kiện để app nhận trong lần poll kế tiếp."""
        self ._events .append (event)

    def poll (self) -> list[VehicleEvent]:
        """Trả các sự kiện đang chờ rồi xóa chúng khỏi hàng đợi."""
        events = self ._events
        self ._events = []
        return events

    def close (self) -> None:
        """Đánh dấu link giả lập đã được đóng."""
        self .closed = True