import os
import sys

# Ensure repo root is on PYTHONPATH so we can import backend
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# Import FastAPI app from backend
from backend.main import app as fastapi_app

# Vercel Python runtime looks for a module-level `app` (ASGI)
app = fastapi_app