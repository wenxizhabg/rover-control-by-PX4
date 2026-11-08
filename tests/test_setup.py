"""US-01/T1: kiểm tra môi trường dự án đã sẵn sàng."""


def test_import_rover_package():
    import rover

    assert rover.__version__ == "0.1.0"


def test_import_pymavlink():
    from pymavlink import mavutil

    assert hasattr(mavutil, "mavlink_connection")