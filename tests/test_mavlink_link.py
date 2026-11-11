"""US-02/T2: kiểm tra MavlinkVehicleLink đọc HEARTBEAT không chờ và giải mã gói tin (tầng driver, dùng giả lập UDP)."""

import time

from pymavlink .dialects .v20 import common as mavlink

from rover .mavlink_link import MavlinkVehicleLink
from rover .types import Heartbeat
from rover .vehicle_info import VehicleInfo
from tests .mavlink_sim import GCS_HEARTBEAT, VEHICLE_HEARTBEAT, HeartbeatSimulator, find_free_port, heartbeat_bytes


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
