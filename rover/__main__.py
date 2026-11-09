"""Cho phép chạy app bằng lệnh "python -m rover ...". Python chạy file này khi gặp "-m rover"; file chỉ gọi main trong cli.py và trả mã thoát của main cho hệ điều hành."""

import sys

from rover .cli import main

sys .exit (main ())