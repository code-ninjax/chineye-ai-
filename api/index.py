import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `api` package is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

# Also ensure the api directory itself is importable (sibling imports fallback)
API_DIR = Path(__file__).resolve().parent
api_dir_str = str(API_DIR)
if api_dir_str not in sys.path:
    sys.path.insert(0, api_dir_str)

try:
    # Prefer package import
    from api.main import app as fastapi_app
    app = fastapi_app
    print("[serverless] api.index loaded app via 'api.main'.")
except Exception as e1:
    try:
        # Fallback to local module import when package import fails
        from main import app as fastapi_app
        app = fastapi_app
        print("[serverless] api.index loaded app via fallback 'main'.")
    except Exception as e2:
        print(f"[serverless] Failed to load FastAPI app. api.main error: {e1}; fallback error: {e2}")
        raise