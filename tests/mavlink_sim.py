"""US-02/T2 & US-03a/T2: bộ giả lập gửi nhận gói tin MAVLink qua UDP dùng cho các test không cần mô phỏng PX4 thật."""

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


def command_ack_bytes (command, result, system_id = 1, component_id = 1):
    """Đóng gói một COMMAND_ACK thành dãy byte MAVLink 2 để giả lập phản hồi từ PX4."""
    sender = mavlink .MAVLink (file = None, srcSystem = system_id, srcComponent = component_id)
    msg = sender .command_ack_encode (command = command, result = result)
    return bytes (msg .pack (sender))


class TwoWayVehicleSimulator:
    """Giả lập xe PX4 hai chiều trên một socket UDP: vừa gửi HEARTBEAT/COMMAND_ACK tới app, vừa đọc COMMAND_LONG app gửi về."""

    def __init__ (self, port, ack_packets = None):
        self .port = port
        # Danh sách các gói COMMAND_ACK gửi sẵn khi bắt đầu chạy (phục vụ test đọc phản hồi).
        self .ack_packets = list (ack_packets or [])
        self .received_commands = []
        self ._lock = threading .Lock ()
        self ._stop = threading .Event ()
        self ._thread = threading .Thread (target = self ._run, daemon = True)

    def _run (self):
        decoder = mavlink .MAVLink (file = None)
        with socket .socket (socket .AF_INET, socket .SOCK_DGRAM) as s:
            # Bind một cổng cục bộ để pymavlink (udpin) biết địa chỉ của giả lập và gửi COMMAND_LONG về đúng socket này.
            s .bind (("127.0.0.1", 0))
            s .settimeout (0.05)

            for pkt in self .ack_packets:
                s .sendto (pkt, ("127.0.0.1", self .port))

            next_hb = 0.0
            while not self ._stop .is_set ():
                now = time .monotonic ()
                if now >= next_hb:
                    s .sendto (VEHICLE_HEARTBEAT, ("127.0.0.1", self .port))
                    next_hb = now + 0.05

                try:
                    data, _ = s .recvfrom (4096)
                except socket .timeout:
                    continue

                # Giải mã gói app gửi về và giữ lại các COMMAND_LONG để test kiểm tra.
                msgs = decoder .parse_buffer (data) or []
                with self ._lock:
                    for msg in msgs:
                        if msg .get_type () == "COMMAND_LONG":
                            self .received_commands .append (msg)

    def wait_commands (self, count = 1, timeout = 1.0):
        """Chờ tối đa timeout giây cho tới khi giả lập nhận đủ count lệnh COMMAND_LONG từ app."""
        deadline = time .monotonic () + timeout
        while time .monotonic () < deadline:
            with self ._lock:
                if len (self .received_commands) >= count:
                    return list (self .received_commands)
            time .sleep (0.02)
        with self ._lock:
            return list (self .received_commands)

    def __enter__ (self):
        self ._thread .start ()
        return self

    def __exit__ (self, *exc):
        self ._stop .set ()
        self ._thread .join ()
