"""US-02/T2 & US-03a/T2: kiểm tra MavlinkVehicleLink đọc HEARTBEAT, gửi lệnh mở/khóa và đọc COMMAND_ACK (tầng driver, dùng giả lập UDP)."""

import time

from pymavlink .dialects .v20 import common as mavlink

from rover .mavlink_link import MavlinkVehicleLink
from rover .types import ArmAck, Heartbeat
from rover .vehicle_info import VehicleInfo
from tests .mavlink_sim import (
    GCS_HEARTBEAT,
    VEHICLE_HEARTBEAT,
    HeartbeatSimulator,
    TwoWayVehicleSimulator,
    command_ack_bytes,
    find_free_port,
    heartbeat_bytes,
)


def test_1_vehicle_heartbeat_returns_heartbeat_event ():
    # Đầu vào: giả lập xe PX4 rover gửi HEARTBEAT tới cổng trống; chờ 0,3 s; gọi poll ().
    port = find_free_port ()
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with HeartbeatSimulator (port, [(VEHICLE_HEARTBEAT, 5)]):
            time .sleep (0.3)
            events = link .poll ()

        # Mong đợi: danh sách khác rỗng; mọi phần tử là Heartbeat với đúng thông tin xe và armed = False (phục vụ AC1).
        assert len (events) > 0
        for ev in events:
            assert isinstance (ev, Heartbeat)
            assert ev .info == VehicleInfo (
                system_id = 1,
                component_id = 1,
                autopilot = "PX4",
                vehicle_type = "GROUND_ROVER",
            )
            assert ev .armed is False
    finally:
        link .close ()


def test_2_armed_flag_in_base_mode_sets_armed_true ():
    # Đầu vào: giả lập xe gửi HEARTBEAT có base_mode bật cờ MAV_MODE_FLAG_SAFETY_ARMED; gọi poll ().
    port = find_free_port ()
    armed_heartbeat = heartbeat_bytes (
        system_id = 1,
        component_id = 1,
        autopilot = mavlink .MAV_AUTOPILOT_PX4,
        vehicle_type = mavlink .MAV_TYPE_GROUND_ROVER,
        base_mode = mavlink .MAV_MODE_FLAG_SAFETY_ARMED,
    )
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with HeartbeatSimulator (port, [(armed_heartbeat, 5)]):
            time .sleep (0.3)
            events = link .poll ()

        # Mong đợi: Heartbeat .armed = True (phục vụ US-03a AC1: giải mã trạng thái khóa xe từ base_mode).
        assert len (events) > 0
        assert events [0] .armed is True
    finally:
        link .close ()


def test_3_gcs_heartbeat_is_ignored ():
    # Đầu vào: chỉ có giả lập QGroundControl (autopilot = INVALID) gửi gói; chờ 0,3 s; gọi poll ().
    port = find_free_port ()
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with HeartbeatSimulator (port, [(GCS_HEARTBEAT, 5)]):
            time .sleep (0.3)
            events = link .poll ()

        # Mong đợi: trả danh sách rỗng [], không nhận nhầm trạm mặt đất là xe (phục vụ AC2).
        assert events == []
    finally:
        link .close ()


def test_4_poll_without_packets_does_not_block ():
    # Đầu vào: không có giả lập nào gửi gói; đo thời gian thực hiện một lần poll ().
    port = find_free_port ()
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        start = time .monotonic ()
        events = link .poll ()
        elapsed = time .monotonic () - start

        # Mong đợi: trả [] trong dưới 0,1 s, vòng lặp app không bị đơ khi mất tín hiệu (phục vụ AC2).
        assert events == []
        assert elapsed < 0.1
    finally:
        link .close ()


def _wait_for_heartbeat (link, timeout = 1.0):
    """Chờ tới khi link .poll () nhận được ít nhất một Heartbeat từ giả lập và gom toàn bộ sự kiện đã nhận."""
    collected = []
    deadline = time .monotonic () + timeout
    while time .monotonic () < deadline:
        events = link .poll ()
        collected .extend (events)
        if any (isinstance (ev, Heartbeat) for ev in events):
            return collected
        time .sleep (0.02)
    raise AssertionError ("Không nhận được HEARTBEAT từ giả lập")


def test_5_send_arm_true_sends_arm_command_long ():
    # Đầu vào: giả lập PX4 hai chiều gửi HEARTBEAT; app poll () thấy xe; gọi send_arm (True).
    port = find_free_port ()
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with TwoWayVehicleSimulator (port) as sim:
            _wait_for_heartbeat (link)
            link .send_arm (True)
            cmds = sim .wait_commands (count = 1, timeout = 1.0)

        # Mong đợi: giả lập nhận được COMMAND_LONG với command = 400, param1 = 1, target_system = 1, target_component = 1 (phục vụ AC1).
        assert len (cmds) == 1
        assert cmds [0] .command == mavlink .MAV_CMD_COMPONENT_ARM_DISARM
        assert cmds [0] .param1 == 1
        assert cmds [0] .target_system == 1
        assert cmds [0] .target_component == 1
    finally:
        link .close ()


def test_6_send_arm_false_sends_disarm_command_long ():
    # Đầu vào: giả lập PX4 hai chiều gửi HEARTBEAT; app poll () thấy xe; gọi send_arm (False).
    port = find_free_port ()
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with TwoWayVehicleSimulator (port) as sim:
            _wait_for_heartbeat (link)
            link .send_arm (False)
            cmds = sim .wait_commands (count = 1, timeout = 1.0)

        # Mong đợi: giả lập nhận được COMMAND_LONG với command = 400, param1 = 0, target_system = 1, target_component = 1 (phục vụ AC2).
        assert len (cmds) == 1
        assert cmds [0] .command == mavlink .MAV_CMD_COMPONENT_ARM_DISARM
        assert cmds [0] .param1 == 0
        assert cmds [0] .target_system == 1
        assert cmds [0] .target_component == 1
    finally:
        link .close ()


def test_7_poll_decodes_arm_command_ack_and_ignores_other_commands ():
    # Đầu vào: giả lập gửi COMMAND_ACK (400, ACCEPTED), COMMAND_ACK (400, DENIED), COMMAND_ACK (176, ACCEPTED); app gọi poll ().
    port = find_free_port ()
    ack_packets = [
        command_ack_bytes (mavlink .MAV_CMD_COMPONENT_ARM_DISARM, mavlink .MAV_RESULT_ACCEPTED),
        command_ack_bytes (mavlink .MAV_CMD_COMPONENT_ARM_DISARM, mavlink .MAV_RESULT_DENIED),
        command_ack_bytes (176, mavlink .MAV_RESULT_ACCEPTED),
    ]
    link = MavlinkVehicleLink (url = f"udpin:127.0.0.1:{port}")
    try:
        with TwoWayVehicleSimulator (port, ack_packets = ack_packets):
            events = _wait_for_heartbeat (link)
            time .sleep (0.05)
            events .extend (link .poll ())

        # Mong đợi: trong kết quả có đúng [ArmAck (True), ArmAck (False)] theo thứ tự, bỏ qua ACK của lệnh 176 (phục vụ AC3).
        acks = [ev for ev in events if isinstance (ev, ArmAck)]
        assert acks == [ArmAck (True), ArmAck (False)]
    finally:
        link .close ()
