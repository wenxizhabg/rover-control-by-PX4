"""US-01/T4: kiểm tra hàm connect: mở cổng UDP, chờ HEARTBEAT của xe, báo ConnectionTimeout khi hết giờ.

Ý tưởng chung của file test này:
1. Không cần mô phỏng PX4. Mỗi test chạy một "giả lập" trên chính máy (localhost): một luồng phụ liên tục gửi gói HEARTBEAT tới một cổng UDP, giống như PX4 gửi tới cổng 14540.
2. Hàm connect nghe ở đúng cổng đó và phải phản ứng đúng với từng tình huống: có xe, không có ai, chỉ có trạm mặt đất, trạm mặt đất gửi trước rồi mới tới xe.
3. Mỗi test dùng một cổng trống ngẫu nhiên, nên không đụng cổng 14540 của mô phỏng thật đang chạy (nếu có).
"""

# socket: thư viện mạng có sẵn của Python, dùng để gửi gói UDP và để tìm một cổng còn trống.
import socket
# threading: chạy giả lập trong một luồng phụ, song song với hàm connect ở luồng chính.
import threading
# time: đo thời gian (kiểm tra hết giờ đúng lúc) và nghỉ giữa các lần gửi.
import time

# pytest .raises dùng để kiểm tra "đoạn code này phải ném ra lỗi X".
import pytest

# Bộ định nghĩa MAVLink 2, tập message chung "common": dùng để đóng gói HEARTBEAT thành dãy byte MAVLink 2, đúng định dạng PX4 gửi.
from pymavlink .dialects .v20 import common as mavlink

# Thứ cần kiểm tra (sẽ viết ở rover/connection.py). Lúc này file đó chưa có, nên chạy pytest sẽ báo lỗi ngay ở dòng import -> đúng như mong đợi.
from rover .connection import ConnectionTimeout, connect
from rover .vehicle_info import VehicleInfo


def find_free_port ():
    """Hỏi hệ điều hành một cổng UDP đang trống trên localhost rồi trả lại số cổng đó (bind vào cổng 0 nghĩa là "cho tôi cổng nào cũng được")."""
    with socket .socket (socket .AF_INET, socket .SOCK_DGRAM) as s:
        s .bind (("127.0.0.1", 0))
        return s .getsockname () [1]


def heartbeat_bytes (system_id, component_id, autopilot, vehicle_type):
    """Đóng gói một HEARTBEAT thành dãy byte MAVLink 2, đúng như một gói UDP mà PX4 hoặc QGroundControl gửi đi."""
    sender = mavlink .MAVLink (file = None, srcSystem = system_id, srcComponent = component_id)
    msg = sender .heartbeat_encode (
        type = vehicle_type,                        # loại thiết bị
        autopilot = autopilot,                      # loại firmware
        base_mode = 0,                              # các cờ trạng thái (không dùng trong test)
        custom_mode = 0,                            # chế độ riêng của PX4 (không dùng trong test)
        system_status = mavlink .MAV_STATE_STANDBY, # trạng thái: đang chờ
    )
    return bytes (msg .pack (sender))


# Hai loại gói dùng trong các test: của xe PX4 rover và của trạm mặt đất (QGroundControl).
VEHICLE_HEARTBEAT = heartbeat_bytes (
    system_id = 1,
    component_id = 1,
    autopilot = mavlink .MAV_AUTOPILOT_PX4,
    vehicle_type = mavlink .MAV_TYPE_GROUND_ROVER,
)
GCS_HEARTBEAT = heartbeat_bytes (
    system_id = 255,
    component_id = 190,
    autopilot = mavlink .MAV_AUTOPILOT_INVALID,
    vehicle_type = mavlink .MAV_TYPE_GCS,
)


class HeartbeatSimulator:
    """Giả lập một bên gửi HEARTBEAT (xe hoặc trạm mặt đất) chạy trong luồng phụ.

    Cách hoạt động:
    1. Nhận vào một "kịch bản": danh sách các bước (gói cần gửi, số giây gửi gói đó). Ví dụ [(GCS_HEARTBEAT, 0.3), (VEHICLE_HEARTBEAT, 5)] nghĩa là gửi gói của trạm mặt đất trong 0,3 giây, sau đó gửi gói của xe trong 5 giây.
    2. Trong mỗi bước, cứ 0,1 giây gửi một gói tới 127.0.0.1:<port>, giống PX4 gửi HEARTBEAT đều đặn.
    3. Dùng với câu lệnh "with": vào khối with thì bắt đầu gửi, ra khỏi khối with thì dừng gửi và đóng socket.
    """

    def __init__ (self, port, script):
        self .port = port
        self .script = script
        self ._stop = threading .Event ()                                  # cờ báo luồng phụ dừng lại
        self ._thread = threading .Thread (target = self ._run, daemon = True)  # daemon: không giữ chương trình lại nếu test kết thúc bất thường

    def _run (self):
        with socket .socket (socket .AF_INET, socket .SOCK_DGRAM) as s:
            for packet, duration in self .script:
                end = time .monotonic () + duration
                while time .monotonic () < end and not self ._stop .is_set ():
                    s .sendto (packet, ("127.0.0.1", self .port))  # gửi một gói UDP, như PX4 gửi tới cổng 14540
                    self ._stop .wait (0.1)                        # nghỉ 0,1 giây (hoặc dừng sớm nếu được báo dừng)

    def __enter__ (self):
        self ._thread .start ()
        return self

    def __exit__ (self, *exc):
        self ._stop .set ()
        self ._thread .join ()


def test_1_ket_noi_duoc_voi_gia_lap_xe_px4 ():
    # Đầu vào: giả lập xe PX4 rover gửi HEARTBEAT (MAVLink 2) liên tục trong 5 giây.
    port = find_free_port ()

    with HeartbeatSimulator (port, [(VEHICLE_HEARTBEAT, 5)]):
        info = connect (url = f"udpin:127.0.0.1:{port}", timeout = 3)

    # Mong đợi: connect nhận ra xe và trả đúng thông tin xe; đồng thời chứng minh app giải mã được gói MAVLink 2.
    assert info == VehicleInfo (
        system_id = 1,
        component_id = 1,
        autopilot = "PX4",
        vehicle_type = "GROUND_ROVER",
    )


def test_2_khong_co_ai_gui_thi_bao_het_gio ():
    # Đầu vào: không có giả lập nào gửi gói; thời gian chờ 0,5 giây.
    port = find_free_port ()
    start = time .monotonic ()

    # Mong đợi: connect ném ConnectionTimeout (đúng AC3: hết giờ thì báo lỗi).
    with pytest .raises (ConnectionTimeout):
        connect (url = f"udpin:127.0.0.1:{port}", timeout = 0.5)

    # Mong đợi: báo lỗi sau khoảng 0,5 giây; không sớm hơn (chờ đủ thời gian) và không treo (không quá lâu).
    elapsed = time .monotonic () - start
    assert 0.4 <= elapsed < 2.0


def test_3_chi_co_tram_mat_dat_thi_van_bao_het_gio ():
    # Đầu vào: chỉ có giả lập trạm mặt đất (QGroundControl) gửi HEARTBEAT; thời gian chờ 0,5 giây.
    port = find_free_port ()

    # Mong đợi: vẫn ném ConnectionTimeout, vì trạm mặt đất không phải xe.
    with HeartbeatSimulator (port, [(GCS_HEARTBEAT, 5)]):
        with pytest .raises (ConnectionTimeout):
            connect (url = f"udpin:127.0.0.1:{port}", timeout = 0.5)


def test_4_bo_qua_tram_mat_dat_va_cho_tiep_toi_khi_gap_xe ():
    # Đầu vào: giả lập trạm mặt đất gửi trong 0,5 giây đầu, sau đó giả lập xe mới bắt đầu gửi.
    port = find_free_port ()

    with HeartbeatSimulator (port, [(GCS_HEARTBEAT, 0.5), (VEHICLE_HEARTBEAT, 5)]):
        info = connect (url = f"udpin:127.0.0.1:{port}", timeout = 3)

    # Mong đợi: connect không dừng ở gói đầu tiên (của trạm mặt đất), mà chờ tiếp và trả thông tin của xe.
    assert info .autopilot == "PX4"
    assert info .vehicle_type == "GROUND_ROVER"