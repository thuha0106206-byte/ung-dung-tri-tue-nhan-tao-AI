# Package backend
import os
import sys

# Đảm bảo backend directory nằm trong sys.path để các router import models, database thuận tiện
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
