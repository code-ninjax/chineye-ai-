import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `api` package is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

try:
    # Import FastAPI app from api package
    from api.main import app as fastapi_app
    # Vercel Python runtime looks for a module-level `app` (ASGI)
    app = fastapi_app
    # Basic startup log (visible in Vercel logs)
    print("[serverless] api.index loaded app successfully.")
except Exception as e:
    # Emit a clear message for startup failures (imports, missing deps)
    print(f"[serverless] Failed to load FastAPI app: {e}")
    raise