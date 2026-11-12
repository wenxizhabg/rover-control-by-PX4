"""Tầng 2 – kiểu dữ liệu dùng chung cho mọi tầng: trạng thái kết nối, hành động người dùng, thông tin xe và các sự kiện driver trả về. File này chỉ định nghĩa kiểu, không có xử lý (hợp đồng API: docs/diagrams/class/class.txt)."""

# Cho phép ghi kiểu ở dạng chuỗi được đánh giá muộn, không cần đúng thứ tự khai báo.
from __future__ import annotations

# dataclass: khai báo lớp chỉ để chứa dữ liệu; Python tự sinh hàm khởi tạo, hàm so sánh == và hàm in ra chuỗi.
from dataclasses import dataclass
# Enum: tập hằng số có tên; khác enum trong C ở chỗ mỗi giá trị là một đối tượng, in ra được tên. auto () tự đánh số, vì code chỉ so sánh theo tên, không dùng con số.
from enum import Enum, auto


class LinkState (Enum):
    """Trạng thái kết nối với xe, do LinkMonitor (US-02) tính từ thời điểm nhận HEARTBEAT."""

    WAITING = auto ()    # chưa nhận HEARTBEAT nào của xe từ lúc mở app
    CONNECTED = auto ()  # HEARTBEAT cuối cách hiện tại không quá 3 s
    LOST = auto ()       # đã từng nhận HEARTBEAT, nhưng quá 3 s chưa có HEARTBEAT mới


class Action (Enum):
    """Việc người dùng muốn làm, đổi từ phím bấm bằng view .action_for."""

    TOGGLE_HELP = auto ()  # ẩn / hiện bảng phím (US-04)
    QUIT = auto ()         # thoát app (US-04)
    ARM = auto ()          # mở khóa xe (US-03a)
    DISARM = auto ()       # khóa xe (US-03a)
    FORWARD = auto ()      # tiến (US-03b)
    BACKWARD = auto ()     # lùi (US-03b)
    TURN_LEFT = auto ()    # quay trái (US-03b)
    TURN_RIGHT = auto ()   # quay phải (US-03b)
    STOP = auto ()         # dừng ngay (US-03b)


@dataclass (frozen = True)
class VehicleInfo:
    """Thông tin cơ bản của một xe, đọc từ HEARTBEAT. frozen = True nghĩa là tạo xong thì không sửa được các trường, tránh vô tình thay đổi thông tin xe ở chỗ khác trong chương trình."""

    system_id: int      # số hiệu của xe trên mạng MAVLink, lấy từ phần đầu (header) của gói
    component_id: int   # số hiệu của bộ phận gửi gói trong xe; 1 là autopilot
    autopilot: str      # tên loại firmware, ví dụ "PX4"
    vehicle_type: str   # tên loại thiết bị, ví dụ "GROUND_ROVER"


@dataclass (frozen = True)
class Heartbeat:
    """Một HEARTBEAT của xe đã được driver giải mã; tầng trên chỉ đọc các trường này, không cần biết MAVLink. frozen = True: tạo xong thì không sửa được."""

    info: VehicleInfo  # thông tin xe (system_id, component_id, autopilot, vehicle_type), lớp của US-01
    armed: bool        # True nếu xe đang mở khóa (cờ MAV_MODE_FLAG_SAFETY_ARMED trong base_mode của HEARTBEAT đang bật)


@dataclass (frozen = True)
class ArmAck:
    """Xe trả lời lệnh mở / khóa (COMMAND_ACK của lệnh MAV_CMD_COMPONENT_ARM_DISARM), do driver giải mã."""

    accepted: bool  # True nếu xe chấp nhận lệnh (result = MAV_RESULT_ACCEPTED); False nếu từ chối


# Kiểu của mỗi phần tử mà VehicleLink .poll () trả về: hoặc một Heartbeat, hoặc một ArmAck.
VehicleEvent = Heartbeat | ArmAck
