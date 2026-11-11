"""US-03a/T1: logic mở / khóa xe (tầng xử lý thuần, không phụ thuộc MAVLink hay phần cứng)."""

from __future__ import annotations

from rover .types import ArmAck, LinkState


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