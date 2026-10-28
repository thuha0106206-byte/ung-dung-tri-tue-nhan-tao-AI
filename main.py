"""
FrogHippo Phone - Root Application Entrypoint
Forwarding request to backend.main:app for seamless separation of concerns.
"""

import sys
import os

# Thêm thư mục backend vào sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    print("[*] Đang khởi chạy FrogHippo Phone Server từ backend...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)