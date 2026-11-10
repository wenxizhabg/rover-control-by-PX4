"""US-04/T0: các interface giữa tầng ứng dụng và driver (hợp đồng Sprint 2, xem docs/diagrams/class/class.txt mục 4.2). Giống HAL trên STM32: RoverApp gọi các hàm ở đây mà không biết bên dưới là MAVLink, curses hay đồng hồ thật; test truyền vào bản giả lập. File này chỉ có chữ ký hàm, không có xử lý."""

# Cho phép ghi kiểu ở dạng chuỗi được đánh giá muộn (ví dụ list [VehicleEvent]) mà không cần đúng thứ tự khai báo.
from __future__ import annotations

# Protocol: khai báo interface chỉ gồm chữ ký hàm. Lớp nào có đủ các hàm đúng tên và tham số thì dùng thay được, không cần kế thừa; giống một struct gồm các con trỏ hàm trong C.
from typing import Protocol

from rover .types import VehicleEvent


class VehicleLink (Protocol):
    """Kênh nói chuyện với xe. Hiện thực thật: MavlinkVehicleLink (US-02/T2, US-03a/T2); giả lập trong test: FakeVehicleLink."""

    def poll (self) -> list [VehicleEvent]:
        """Đọc mọi gói đang chờ, không chờ gói mới; chỉ trả gói của xe (bỏ gói autopilot = INVALID như QGroundControl); không có gói nào thì trả danh sách rỗng."""
        ...

    def send_arm (self, arm: bool) -> None:
        """Gửi lệnh mở khóa (arm = True) hoặc khóa (arm = False) tới xe đã thấy gần nhất; xe trả lời sau, qua ArmAck trong poll ()."""
        ...

    def close (self) -> None:
        """Đóng cổng kết nối."""
        ...


class Terminal (Protocol):
    """Màn hình và bàn phím. Hiện thực thật: CursesTerminal (US-04/T3); giả lập trong test: FakeTerminal."""

    def read_key (self) -> str | None:
        """Trả phím vừa bấm (một ký tự, ví dụ "h"); chờ tối đa 50 ms, không có phím thì trả None."""
        ...

    def draw (self, lines: list [str]) -> None:
        """Xóa và vẽ lại toàn bộ khung bằng các dòng lines; dòng dài hơn màn hình thì cắt bớt."""
        ...

    def close (self) -> None:
        """Trả terminal về bình thường: hiện con trỏ, chữ gõ hiện lại lên màn hình."""
        ...


class Clock (Protocol):
    """Đồng hồ. Hiện thực thật: SystemClock (US-04/T3); giả lập trong test: FakeClock."""

    def now (self) -> float:
        """Thời điểm hiện tại tính bằng giây, chỉ tăng (không lùi khi đổi giờ hệ thống)."""
        ...