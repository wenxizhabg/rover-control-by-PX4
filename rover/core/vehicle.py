"""Tầng 2 – trạng thái của xe: kết nối (theo nhịp HEARTBEAT) và mở / khóa xe."""

from __future__ import annotations

from rover .core .model import ArmAck, LinkState

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


class ArmControl:
    """Quản lý trạng thái khóa xe theo HEARTBEAT, kiểm tra điều kiện gửi lệnh mở / khóa và tạo thông báo phản hồi."""

    def __init__ (self) -> None:
        # Trạng thái khóa thật của xe lấy từ HEARTBEAT; None khi chưa nhận gói nào.
        self ._armed: bool | None = None
        # Ghi nhớ lệnh gửi gần nhất (True = mở khóa, False = khóa) để on_ack trả đúng thông báo.
        self ._last_arm_request: bool = True

    @property
    def armed (self) -> bool | None:
        """Trạng thái khóa theo HEARTBEAT gần nhất; None nếu chưa có HEARTBEAT."""
        return self ._armed

    def on_heartbeat (self, armed: bool) -> None:
        """Cập nhật trạng thái khóa của xe từ cờ armed trong HEARTBEAT."""
        self ._armed = armed

    def request (self, arm: bool, link_state: LinkState) -> tuple [bool, str]:
        """Kiểm tra có được gửi lệnh mở (arm = True) hoặc khóa (arm = False) hay không; trả (gửi?, thông báo)."""
        # Chỉ gửi lệnh khi đang kết nối xe; mất kết nối hoặc đang chờ thì chặn ngay và báo người dùng.
        if link_state != LinkState .CONNECTED:
            return (False, "Chưa kết nối xe")

        # Lưu lại loại lệnh vừa được phép gửi để đối chiếu khi xe gửi COMMAND_ACK về.
        self ._last_arm_request = arm
        action_text = "mở khóa" if arm else "khóa"
        return (True, f"Đã gửi lệnh {action_text}")

    def on_ack (self, ack: ArmAck) -> str:
        """Tạo thông báo tiếng Việt theo phản hồi COMMAND_ACK của xe cho lệnh gửi gần nhất."""
        action_text = "mở khóa" if self ._last_arm_request else "khóa"
        if ack .accepted:
            return f"Xe chấp nhận lệnh {action_text}"
        return f"Xe từ chối lệnh {action_text}"
