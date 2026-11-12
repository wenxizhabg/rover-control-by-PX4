"""Giả lập tầng 3 dùng trong test: terminal, đồng hồ và kênh xe (US-04/T4, US-02/T3, US-03a/T3, US-03b/T3)."""

from rover .core .model import VehicleEvent


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

    def __init__ (self, keys: list[str | None] | None = None) -> None:
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
    """Kênh xe giả lập, trả các sự kiện đã xếp sẵn cho lần poll kế tiếp và ghi lại lệnh gửi đi."""

    def __init__ (self) -> None:
        self ._events: list[VehicleEvent] = []
        self .sent_arm: list[bool] = []
        self .sent_drive: list[tuple[float, float]] = []
        self .manual_mode_requests: int = 0
        self .closed = False

    def push (self, event: VehicleEvent) -> None:
        """Xếp một sự kiện để app nhận trong lần poll kế tiếp."""
        self ._events .append (event)

    def poll (self) -> list[VehicleEvent]:
        """Trả các sự kiện đang chờ rồi xóa chúng khỏi hàng đợi."""
        events = self ._events
        self ._events = []
        return events

    def send_arm (self, arm: bool) -> None:
        """Ghi lại lệnh mở khóa (True) hoặc khóa (False) để test kiểm tra."""
        self .sent_arm .append (arm)

    def send_drive (self, forward: float, turn: float) -> None:
        """Ghi lại mức lái (forward, turn) đã gửi để test kiểm tra."""
        self .sent_drive .append ((forward, turn))

    def send_manual_mode (self) -> None:
        """Đếm số lần yêu cầu xe chuyển sang chế độ Manual."""
        self .manual_mode_requests += 1

    def close (self) -> None:
        """Đánh dấu link giả lập đã được đóng."""
        self .closed = True