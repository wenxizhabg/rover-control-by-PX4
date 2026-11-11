"""US-02/T1: logic xác định trạng thái kết nối với xe (tầng xử lý thuần, không phụ thuộc MAVLink hay đồng hồ thật)."""

from rover .types import LinkState

# Ngưỡng thời gian mất kết nối (giây); quá 3.0 s không có HEARTBEAT thì coi là mất kết nối.
LINK_TIMEOUT_S: float = 3.0


class LinkMonitor:
    """Theo dõi nhịp HEARTBEAT nhận được từ xe và tính toán trạng thái kết nối theo thời gian."""

    def __init__ (self, timeout_s: float = LINK_TIMEOUT_S) -> None:
        self .timeout_s = timeout_s
        self ._last_heartbeat_time: float | None = None
        self ._heartbeat_count: int = 0

    def on_heartbeat (self, now: float) -> None:
        """Ghi nhận một HEARTBEAT của xe vừa nhận được tại thời điểm now."""
        self ._last_heartbeat_time = now
        self ._heartbeat_count += 1

    @property
    def heartbeat_count (self) -> int:
        """Số HEARTBEAT của xe đã nhận được từ lúc mở app."""
        return self ._heartbeat_count

    def seconds_since_last (self, now: float) -> float | None:
        """Số giây trôi qua từ lần cuối nhận HEARTBEAT; trả về None nếu chưa từng nhận gói nào."""
        if self ._last_heartbeat_time is None:
            return None
        return now - self ._last_heartbeat_time

    def state (self, now: float) -> LinkState:
        """Tính trạng thái kết nối: WAITING nếu chưa có gói, LOST nếu quá timeout_s, ngược lại là CONNECTED."""
        if self ._last_heartbeat_time is None:
            return LinkState .WAITING

        elapsed = now - self ._last_heartbeat_time
        # Đúng ngưỡng 3.0 s vẫn là CONNECTED; chỉ khi lớn hơn 3.0 s mới tính là LOST.
        if elapsed > self .timeout_s:
            return LinkState .LOST

        return LinkState .CONNECTED
