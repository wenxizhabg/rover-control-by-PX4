"""US-02/T2: bộ giả lập gửi nhận gói tin MAVLink qua UDP dùng cho các test không cần mô phỏng PX4 thật."""

import socket
import threading
import time

from pymavlink .dialects .v20 import common as mavlink


def find_free_port ():
    """Hỏi hệ điều hành một cổng UDP đang trống trên localhost rồi trả lại số cổng đó (bind vào cổng 0 nghĩa là "cho tôi cổng nào cũng được")."""
    with socket .socket (socket .AF_INET, socket .SOCK_DGRAM) as s:
        s .bind (("127.0.0.1", 0))
        return s .getsockname () [1]


def heartbeat_bytes (system_id, component_id, autopilot, vehicle_type, base_mode = 0):
    """Đóng gói một HEARTBEAT thành dãy byte MAVLink 2, đúng như một gói UDP mà PX4 hoặc QGroundControl gửi đi."""
    sender = mavlink .MAVLink (file = None, srcSystem = system_id, srcComponent = component_id)
    msg = sender .heartbeat_encode (
        type = vehicle_type,                        # loại thiết bị
        autopilot = autopilot,                      # loại firmware
        base_mode = base_mode,                      # các cờ trạng thái (bit MAV_MODE_FLAG_SAFETY_ARMED = 128)
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
