"""
File: run_tests.py
Script chạy kiểm thử toàn diện hệ thống FrogHippo Phone
"""
import sys
import os

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    print("[*] Đang khởi chạy bộ kiểm thử tự động FrogHippo Phone...")
    exit_code = os.system("python tests/test_system.py")
    sys.exit(exit_code)
