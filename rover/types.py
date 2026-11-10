"""US-04/T0: kiểu dữ liệu dùng chung giữa các tầng của app (hợp đồng Sprint 2, xem docs/diagrams/class/class.txt mục 4.1). File này chỉ định nghĩa kiểu, không có xử lý."""

# Cho phép ghi kiểu ở dạng chuỗi được đánh giá muộn: nhờ vậy dòng import VehicleInfo bên dưới chỉ cần khi kiểm tra kiểu, không chạy lúc chương trình chạy.
from __future__ import annotations

# dataclass: khai báo lớp chỉ để chứa dữ liệu; Python tự sinh hàm khởi tạo, hàm so sánh == và hàm in ra chuỗi.
from dataclasses import dataclass
# Enum: tập hằng số có tên; khác enum trong C ở chỗ mỗi giá trị là một đối tượng, in ra được tên. auto () tự đánh số, vì code chỉ so sánh theo tên, không dùng con số.
from enum import Enum, auto
# TYPE_CHECKING chỉ bằng True khi công cụ kiểm tra kiểu đọc file, bằng False khi chạy thật.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # vehicle_info.py import pymavlink; chỉ import khi kiểm tra kiểu để tầng xử lý dùng file này mà không kéo theo pymavlink (quy tắc chiều gọi, class.txt mục 3).
    from rover .vehicle_info import VehicleInfo


class LinkState (Enum):
    """Trạng thái kết nối với xe, do LinkMonitor (US-02) tính từ thời điểm nhận HEARTBEAT."""

    WAITING = auto ()    # chưa nhận HEARTBEAT nào của xe từ lúc mở app
    CONNECTED = auto ()  # HEARTBEAT cuối cách hiện tại không quá 3 s
    LOST = auto ()       # đã từng nhận HEARTBEAT, nhưng quá 3 s chưa có HEARTBEAT mới


class Action (Enum):
    """Việc người dùng muốn làm, đổi từ phím bấm bằng keymap .action_for."""

    TOGGLE_HELP = auto ()  # ẩn / hiện bảng phím (US-04)
    QUIT = auto ()         # thoát app (US-04)
    ARM = auto ()          # mở khóa xe (US-03a)
    DISARM = auto ()       # khóa xe (US-03a)


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