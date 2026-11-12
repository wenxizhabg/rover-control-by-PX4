"""Điểm vào của "python -m rover": Python chạy file này khi gặp "-m rover"; file chỉ chạy app và trả mã thoát của app cho hệ điều hành."""

import sys

from rover .app import run_app

sys .exit (run_app ())
