import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `backend` is importable in serverless
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

# Import FastAPI app from backend
from backend.main import app as fastapi_app

# Vercel Python runtime looks for a module-level `app` (ASGI)
app = fastapi_app