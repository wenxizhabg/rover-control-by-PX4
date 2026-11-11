"""US-04/T3: đồng hồ đơn điệu của hệ thống."""

import time


class SystemClock:
    """Đồng hồ hệ thống chỉ tăng, không phụ thuộc giờ lịch."""

    def now (self) -> float:
        """Trả thời gian hiện tại theo giây từ time.monotonic ()."""
        return time .monotonic ()
