"""
FrogHippo Phone - Quick Start Runner
Chạy: python run.py
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("       FROGHIPPO PHONE - HE THONG QUAN LY TRUNG TAM SUA CHUA")
    print("       Server khoi dong tai: http://127.0.0.1:8000")
    print("       Giao dien Khach hang : http://127.0.0.1:8000/")
    print("       Giao dien Tong hop   : http://127.0.0.1:8000/app")
    print("       Swagger API Docs     : http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
