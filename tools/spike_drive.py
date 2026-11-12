"""Spike US-03b/T0: thử lái rover PX4 bằng MANUAL_CONTROL qua cổng 14540. Script thử, không thuộc app, không có test; mỗi lần chạy làm một thí nghiệm."""

import math
import os
import sys
import time

# PX4 gửi MAVLink 2; bật trước khi import pymavlink, giống app.
os .environ ["MAVLINK20"] = "1"

from pymavlink import mavutil
from pymavlink .dialects .v20 import common as mavlink

# Cùng cổng với app (instance Onboard của PX4 SITL). Biến môi trường SPIKE_URL chỉ để thử script với giả lập.
URL = os .environ .get ("SPIKE_URL", "udpin:0.0.0.0:14540")

# Main mode của PX4 nằm ở byte thứ 3 của custom_mode trong HEARTBEAT; sub mode của AUTO nằm ở byte thứ 4.
MAIN_MODES = {1: "MANUAL", 2: "ALTCTL", 3: "POSCTL", 4: "AUTO", 5: "ACRO", 6: "OFFBOARD", 7: "STABILIZED"}
AUTO_SUB_MODES = {1: "READY", 2: "TAKEOFF", 3: "LOITER", 4: "MISSION", 5: "RTL", 6: "LAND"}
MANUAL = 1

conn = mavutil .mavlink_connection (URL, dialect = "common")
start_time = time .monotonic ()
last_state = None
SYS = COMP = None
# Vị trí (x bắc, y đông, mét) và hướng xe (yaw, độ; tăng = quay phải) mới nhất, đọc từ LOCAL_POSITION_NED và ATTITUDE.
pose = {"x": 0.0, "y": 0.0, "yaw": 0.0}


def log (text):
    """In một dòng kèm số giây từ lúc chạy script, để đo thời gian (Q3)."""
    print (f"[{time .monotonic () - start_time:6.2f} s] {text}", flush = True)


def mode_name (custom_mode):
    """Đổi custom_mode của HEARTBEAT thành tên chế độ, ví dụ MANUAL hoặc AUTO/LOITER."""
    main = (custom_mode >> 16) & 0xFF
    sub = (custom_mode >> 24) & 0xFF
    name = MAIN_MODES .get (main, f"?{main}")
    if main == 4:
        name += "/" + AUTO_SUB_MODES .get (sub, f"?{sub}")
    return name


def handle (msg):
    """In những gói cần quan sát: đổi chế độ / khóa (HEARTBEAT), trả lời lệnh (COMMAND_ACK), lời PX4 báo (STATUSTEXT)."""
    global last_state
    msg_type = msg .get_type ()
    if msg_type == "HEARTBEAT":
        if msg .autopilot == mavlink .MAV_AUTOPILOT_INVALID:
            return
        armed = bool (msg .base_mode & mavlink .MAV_MODE_FLAG_SAFETY_ARMED)
        state = (mode_name (msg .custom_mode), armed)
        # Chỉ in khi chế độ hoặc trạng thái khóa thay đổi, tránh mỗi giây một dòng.
        if state != last_state:
            log (f"HEARTBEAT   : chế độ {state [0]}, {'ĐÃ MỞ KHÓA' if armed else 'ĐÃ KHÓA'}")
            last_state = state
    elif msg_type == "COMMAND_ACK":
        log (f"COMMAND_ACK : lệnh {msg .command} -> {mavlink .enums ['MAV_RESULT'] [msg .result] .name}")
    elif msg_type == "STATUSTEXT":
        log (f"STATUSTEXT  : {msg .text}")
    elif msg_type == "LOCAL_POSITION_NED":
        pose ["x"], pose ["y"] = msg .x, msg .y
    elif msg_type == "ATTITUDE":
        pose ["yaw"] = math .degrees (msg .yaw)


def pump ():
    """Đọc hết gói đang chờ, không chờ gói mới."""
    while True:
        msg = conn .recv_match (blocking = False)
        if msg is None:
            return
        handle (msg)


def wait_vehicle ():
    """Chờ HEARTBEAT của xe (bỏ QGroundControl) để biết system_id, component_id và địa chỉ UDP của xe."""
    log (f"Nghe {URL}, chờ HEARTBEAT của xe ...")
    while True:
        msg = conn .recv_match (type = "HEARTBEAT", blocking = True, timeout = 5)
        if msg is None:
            log ("Chưa thấy xe: mô phỏng đã bật chưa?")
            continue
        if msg .autopilot != mavlink .MAV_AUTOPILOT_INVALID:
            handle (msg)
            log (f"Thấy xe: system {msg .get_srcSystem ()}, component {msg .get_srcComponent ()}")
            return msg .get_srcSystem (), msg .get_srcComponent ()


def command (cmd, param1 = 0, param2 = 0):
    """Gửi một COMMAND_LONG tới xe; kết quả về sau qua COMMAND_ACK."""
    conn .mav .command_long_send (SYS, COMP, cmd, 0, param1, param2, 0, 0, 0, 0, 0)


def set_mode (main_mode):
    """MAV_CMD_DO_SET_MODE (176): param1 = 1 (dùng custom mode), param2 = main mode của PX4."""
    log (f"GỬI        : đổi chế độ -> {MAIN_MODES [main_mode]}")
    command (mavlink .MAV_CMD_DO_SET_MODE, mavlink .MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, main_mode)


def arm (on):
    """MAV_CMD_COMPONENT_ARM_DISARM (400), giống send_arm của app."""
    log (f"GỬI        : {'mở khóa' if on else 'khóa'}")
    command (mavlink .MAV_CMD_COMPONENT_ARM_DISARM, 1 if on else 0)


def report (before):
    """In xe đã đi bao xa (theo hướng ban đầu của xe: dương = tiến) và quay bao nhiêu độ (dương = quay phải) so với before."""
    dx, dy = pose ["x"] - before ["x"], pose ["y"] - before ["y"]
    heading = math .radians (before ["yaw"])
    # Chiếu độ dời lên hướng mũi xe lúc bắt đầu: dương là đi về phía trước, âm là lùi.
    forward = dx * math .cos (heading) + dy * math .sin (heading)
    turn = (pose ["yaw"] - before ["yaw"] + 180) % 360 - 180
    log (f"  KẾT QUẢ   : tiến {forward:+.2f} m (tổng dời {math .hypot (dx, dy):.2f} m), quay {turn:+.1f} độ")


def drive (seconds, z = 500, y = 0, x = 0, r = 0, hz = 10):
    """Gửi MANUAL_CONTROL đều hz lần/giây trong seconds giây. Giả thuyết: z = 500 là đứng yên, z > 500 tiến, y là quay."""
    log (f"GỬI        : MANUAL_CONTROL x={x} y={y} z={z} r={r}, {hz} lần/giây trong {seconds} s")
    before = dict (pose)
    end = time .monotonic () + seconds
    while time .monotonic () < end:
        conn .mav .manual_control_send (SYS, x, y, z, r, 0)
        pump ()
        time .sleep (1 / hz)
    report (before)


def idle (seconds):
    """Không gửi gì, chỉ đọc gói, để xem PX4 làm gì."""
    log (f"NGỪNG GỬI  : chỉ quan sát {seconds} s")
    before = dict (pose)
    end = time .monotonic () + seconds
    while time .monotonic () < end:
        pump ()
        time .sleep (0.05)
    report (before)


def run (steps):
    """Khung chung cho E3–E5, E7: gửi đứng yên, đổi Manual, mở khóa, chạy từng bước (z, y, giây), dừng, khóa. Gửi liên tục từ đầu đến cuối để không bị mất tay điều khiển."""
    drive (1)
    set_mode (MANUAL)
    drive (1)
    arm (True)
    drive (1)
    for z, y, seconds in steps:
        drive (seconds, z = z, y = y)
    drive (2)
    arm (False)
    drive (1)


def e1 ():
    """Q2: đổi sang Manual khi CHƯA gửi MANUAL_CONTROL."""
    set_mode (MANUAL)
    idle (3)


def e1b ():
    """Q2: đổi sang Manual khi ĐANG gửi MANUAL_CONTROL đứng yên."""
    drive (1)
    set_mode (MANUAL)
    drive (3)


def e2a ():
    """Q2: ở Manual, mở khóa khi KHÔNG gửi MANUAL_CONTROL."""
    set_mode (MANUAL)
    idle (1)
    arm (True)
    idle (3)
    arm (False)
    idle (1)


def e2b ():
    """Q2: ở Manual, mở khóa khi ĐANG gửi MANUAL_CONTROL đứng yên."""
    drive (1)
    set_mode (MANUAL)
    drive (1)
    arm (True)
    drive (3)
    arm (False)
    drive (1)


def e2c ():
    """Q2: mở khóa ở chế độ mặc định như app hiện tại (không gửi gì), rồi mới gửi MANUAL_CONTROL, đổi Manual và lái thử."""
    arm (True)
    idle (2)
    drive (1)
    set_mode (MANUAL)
    drive (1)
    drive (1, z = 750)
    drive (2)
    arm (False)
    drive (1)


def e6 ():
    """Q3: đang chạy chậm thì ngừng gửi hẳn: sau bao lâu PX4 báo mất tay điều khiển, chuyển chế độ nào, xe có dừng không."""
    drive (1)
    set_mode (MANUAL)
    drive (1)
    arm (True)
    drive (1)
    drive (1, z = 650)
    idle (5)
    drive (1)
    set_mode (MANUAL)
    drive (1)
    arm (False)
    drive (1)


def e6b ():
    """Q3: gửi đứng yên ở 5 lần/giây rồi 2 lần/giây: tần số nào đủ để không bị mất tay điều khiển."""
    drive (1)
    set_mode (MANUAL)
    drive (1)
    arm (True)
    drive (3, hz = 5)
    drive (3, hz = 2)
    drive (2)
    arm (False)
    drive (1)


EXPERIMENTS = {
    "e1": e1,
    "e1b": e1b,
    "e2a": e2a,
    "e2b": e2b,
    "e2c": e2c,
    "e3": lambda: run ([(750, 0, 1)]),                                    # Q1, Q4: tiến 1 s
    "e4": lambda: run ([(250, 0, 1)]),                                    # Q4: lùi 1 s
    "e5": lambda: run ([(500, 500, 1), (500, 0, 2), (500, -500, 1)]),     # Q4: y dương rồi y âm
    "e6": e6,
    "e6b": e6b,
    "e7": lambda: run ([(600, 0, 1), (500, 0, 2), (1000, 0, 1), (500, 0, 2), (500, 300, 1), (500, 0, 2), (500, 800, 1)]),  # Q6
}


if __name__ == "__main__":
    name = sys .argv [1] if len (sys .argv) > 1 else ""
    if name not in EXPERIMENTS:
        print ("Cách dùng: python tools/spike_drive.py <" + " | ".join (EXPERIMENTS) + ">")
        sys .exit (2)
    try:
        SYS, COMP = wait_vehicle ()
        # Đọc gói 0.5 s để có vị trí, hướng xe thật trước khi đo.
        settle_end = time .monotonic () + 0.5
        while time .monotonic () < settle_end:
            pump ()
            time .sleep (0.02)
        log (f"Vị trí đầu  : x {pose ['x']:+.2f} m, y {pose ['y']:+.2f} m, hướng {pose ['yaw']:+.1f} độ")
        EXPERIMENTS [name] ()
        log ("Xong.")
    finally:
        conn .close ()
