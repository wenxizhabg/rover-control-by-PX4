"""US-01/T5: kiểm tra lệnh CLI "python -m rover connect": đọc tùy chọn, gọi connect, in kết quả và trả mã thoát.

Ý tưởng chung của file test này:
1. Không cần mô phỏng, không cần mạng. Mỗi test truyền vào main một hàm giả lập thay cho connect thật (phần mạng đã được kiểm ở T4).
2. Hàm giả lập ghi lại url, timeout mà main truyền cho nó, rồi trả VehicleInfo hoặc ném ConnectionTimeout theo kịch bản của test.
3. capsys là công cụ có sẵn của pytest: bắt lại những gì chương trình in ra stdout và stderr để test kiểm tra nội dung.
"""

from rover .cli import main
from rover .connection import DEFAULT_TIMEOUT, DEFAULT_URL, ConnectionTimeout
from rover .vehicle_info import VehicleInfo


class FakeConnect:
    """Hàm giả lập thay cho connect thật.

    Cách hoạt động:
    1. Tạo với một kết quả: hoặc một VehicleInfo (giả lập kết nối được), hoặc một lỗi (giả lập hết giờ).
    2. Khi main gọi nó như gọi connect (url = ..., timeout = ...), nó ghi lại url và timeout vào self .calls để test kiểm tra.
    3. Sau đó trả VehicleInfo, hoặc ném lỗi, đúng như kết quả đã định.
    """

    def __init__ (self, result):
        self .result = result
        self .calls = []  # danh sách các lần được gọi, mỗi lần là (url, timeout)

    def __call__ (self, url, timeout):
        self .calls .append ((url, timeout))
        if isinstance (self .result, Exception):
            raise self .result
        return self .result


# Thông tin xe mô phỏng, dùng chung cho các test.
ROVER = VehicleInfo (
    system_id = 1,
    component_id = 1,
    autopilot = "PX4",
    vehicle_type = "GROUND_ROVER",
)


def test_1_ket_noi_thanh_cong_in_thong_tin_xe_va_tra_ma_0 (capsys):
    # Đầu vào: người dùng gõ "connect"; hàm giả lập trả thông tin xe.
    fake = FakeConnect (ROVER)

    code = main (["connect"], connect_fn = fake)

    # Mong đợi: stdout có đúng dòng của AC2; không có lỗi; mã thoát 0.
    out = capsys .readouterr ()
    assert "Đã kết nối: system=1 component=1 autopilot=PX4 type=GROUND_ROVER" in out .out
    assert out .err == ""
    assert code == 0


def test_2_het_gio_in_loi_ra_stderr_va_tra_ma_khac_0 (capsys):
    # Đầu vào: người dùng gõ "connect"; hàm giả lập ném ConnectionTimeout như khi không có xe.
    fake = FakeConnect (ConnectionTimeout ("Không nhận được heartbeat từ xe sau 10 s"))

    code = main (["connect"], connect_fn = fake)

    # Mong đợi: thông báo lỗi của AC3 nằm ở stderr; stdout trống; mã thoát khác 0.
    out = capsys .readouterr ()
    assert "Không nhận được heartbeat từ xe sau 10 s" in out .err
    assert out .out == ""
    assert code != 0


def test_3_khong_go_tuy_chon_thi_dung_gia_tri_mac_dinh ():
    # Đầu vào: người dùng chỉ gõ "connect", không có --url, --timeout.
    fake = FakeConnect (ROVER)

    main (["connect"], connect_fn = fake)

    # Mong đợi: connect được gọi đúng 1 lần, với cổng 14540 của PX4 SITL và thời gian chờ 10 giây (lấy từ connection.py).
    assert fake .calls == [(DEFAULT_URL, DEFAULT_TIMEOUT)]
    assert DEFAULT_URL == "udpin:0.0.0.0:14540"
    assert DEFAULT_TIMEOUT == 10


def test_4_tuy_chon_url_va_timeout_duoc_truyen_dung_xuong_connect ():
    # Đầu vào: người dùng gõ thêm --timeout 3 và --url khác.
    fake = FakeConnect (ROVER)

    main (["connect", "--timeout", "3", "--url", "udpin:127.0.0.1:15000"], connect_fn = fake)

    # Mong đợi: connect nhận đúng timeout = 3 (AC4) và url người dùng gõ.
    assert fake .calls == [("udpin:127.0.0.1:15000", 3)]

def test_5_khong_co_lenh_con_thi_chay_app ():
    calls = []

    def fake_app ():
        calls .append (True)
        return 0

    assert main ([], app_fn = fake_app) == 0
    assert calls == [True]