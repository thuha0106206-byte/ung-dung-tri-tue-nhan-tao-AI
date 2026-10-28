import os
from pathlib import Path

# Thư mục gốc dự án (quan_ly_sua_chua)
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục Frontend
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"

def get_frontend_file(filename: str) -> str:
    """Trả về đường dẫn tuyệt đối của file trong frontend/, fallback nếu ở root."""
    frontend_path = FRONTEND_DIR / filename
    if frontend_path.exists():
        return str(frontend_path)
    root_path = BASE_DIR / filename
    if root_path.exists():
        return str(root_path)
    return str(frontend_path)
